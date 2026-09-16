"""
Verify the native Windows (CPU) environment for these RL demo notebooks.

Run with the rl-robotics conda environment's Python, e.g.:

    conda activate rl-robotics
    python scripts/windows/verify-native.py

Checks Python, PyTorch (CPU), gymnasium rendering through pygame-ce, OpenCV video writing,
Stable-Baselines3, Weights & Biases (offline) and Ax. Exit code is 0 when every check passes,
1 otherwise.
"""

import importlib.metadata
import logging
import math
import os
import sys
import tempfile
import time
import traceback
import warnings

# Non-ASCII output (progress marks, warnings) raises UnicodeEncodeError under the cp1252 console
# encoding as soon as the output is redirected to a file or a pipe.
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("WANDB_MODE", "offline")  # no login or network needed to verify the package
os.environ.setdefault("WANDB_SILENT", "true")

_failures = []


def check(name, fn):
    """Run one check, print PASS/FAIL, and collect failures."""
    print(f"[ {name} ]")
    try:
        fn()
        print("  PASS\n")
    except Exception as exc:  # noqa: BLE001
        _failures.append(name)
        print(f"  FAIL: {exc}")
        traceback.print_exc()
        print()


# ------------------------------------------------------------------------------
# Checks

def check_python():
    print(f"  {sys.version.split()[0]}  ({sys.executable})")
    assert sys.version_info[:2] == (3, 12), "expected Python 3.12 (see setup-native.ps1)"


def check_torch():
    import torch
    print(f"  torch {torch.__version__}  (threads: {torch.get_num_threads()})")
    x = torch.randn(1024, 1024)
    t0 = time.time()
    y = (x @ x).sum().item()
    print(f"  1024x1024 matmul on CPU: {1000 * (time.time() - t0):.1f} ms, finite={math.isfinite(y)}")
    assert math.isfinite(y)
    if torch.cuda.is_available():
        print(f"  CUDA build detected ({torch.cuda.get_device_name(0)}); the notebooks run fine on the CPU")
    else:
        print("  CPU-only build (expected)")


def check_gymnasium_render():
    import gymnasium as gym

    # pygame and pygame-ce install the same files, so upstream pygame on top of pygame-ce (for
    # example from "pip install gymnasium[classic-control]") silently overwrites it. The imported
    # module cannot tell them apart; the distribution metadata can.
    try:
        importlib.metadata.version("pygame")
    except importlib.metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError("upstream pygame is installed over pygame-ce: run "
                             "'pip uninstall pygame' and then 'pip install --force-reinstall pygame-ce==2.5.8'")
    print(f"  gymnasium {gym.__version__}, pygame-ce {importlib.metadata.version('pygame-ce')}")

    # The notebooks render off-screen (render_mode="rgb_array") and record the frames with OpenCV
    for env_id, shape in (("CartPole-v1", (400, 600, 3)), ("Pendulum-v1", (500, 500, 3))):
        env = gym.make(env_id, render_mode="rgb_array")
        env.reset(seed=0)
        frame = env.render()
        assert frame.shape == shape, f"{env_id}: unexpected frame shape {frame.shape}"
        env.step(env.action_space.sample())
        env.close()
    print("  CartPole-v1 and Pendulum-v1 rendered off-screen through pygame")


def check_opencv_video():
    import cv2
    import numpy as np
    print(f"  opencv {cv2.__version__}")
    frame = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.putText(frame, "verify", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    with tempfile.TemporaryDirectory() as d:
        video = os.path.join(d, "demo.mp4")
        writer = cv2.VideoWriter(video, cv2.VideoWriter.fourcc(*"mp4v"), 30, (500, 500))
        for _ in range(5):
            writer.write(frame)
        writer.release()
        cap = cv2.VideoCapture(video)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        ok, first = cap.read()
        cap.release()
        assert frames == 5 and ok, f"cv2.VideoWriter wrote {frames} frames, expected 5"
        assert first.max() > 0, "decoded frame is blank"
    print("  mp4v VideoWriter -> VideoCapture round trip: 5 frames, caption visible")


def check_sb3():
    import gymnasium as gym
    import stable_baselines3 as sb3
    print(f"  stable-baselines3 {sb3.__version__}")
    with tempfile.TemporaryDirectory() as d:
        # DQN on CartPole as in rl-demo-cartpole.ipynb, PPO on Pendulum as in the pendulum notebooks
        env = gym.make("CartPole-v1")
        dqn = sb3.DQN("MlpPolicy", env, learning_starts=32, train_freq=8, verbose=0, device="cpu")
        dqn.learn(total_timesteps=64)
        dqn.save(os.path.join(d, "dqn"))
        sb3.DQN.load(os.path.join(d, "dqn"), device="cpu")
        env.close()

        env = gym.make("Pendulum-v1")
        ppo = sb3.PPO("MlpPolicy", env, n_steps=64, batch_size=32, n_epochs=1, verbose=0, device="cpu")
        ppo.learn(total_timesteps=64)
        ppo.save(os.path.join(d, "ppo"))
        sb3.PPO.load(os.path.join(d, "ppo"), device="cpu")
        env.close()
    print("  DQN and PPO: learn, save, load on the CPU")


def check_wandb():
    import shutil
    import wandb
    print(f"  wandb {wandb.__version__}")
    # Not TemporaryDirectory(): wandb's background service keeps its log files open for a moment
    # after finish(), and on Windows deleting an open file raises PermissionError.
    d = tempfile.mkdtemp(prefix="wandb-verify-")
    try:
        run = wandb.init(project="verify-native", mode="offline", dir=d)
        run.log({"reward": 1.0})
        run.finish()
        wandb.teardown()  # stops the service process so the files are released
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("  offline run: init, log, finish (the HPO notebook additionally needs 'wandb login')")


def check_ax():
    from ax.service.ax_client import AxClient
    from ax.service.utils.instantiation import ObjectiveProperties
    from ax.utils.common.logger import set_ax_logger_levels
    set_ax_logger_levels(logging.WARNING)  # Ax gives every logger its own INFO level
    print(f"  ax-platform {importlib.metadata.version('ax-platform')}")

    # The HPO notebook's Ax calls; objectives= replaces the objective_name= that Ax 0.3.7 removed.
    # Ax 1.3 deprecates AxClient and announces its removal in 1.4.0. The notebook is built on it, so
    # the environment stays on ax-platform 1.3.x and the warning is expected here.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        client = AxClient(verbose_logging=False)
    client.create_experiment(
        name="verify",
        parameters=[{"name": "lr", "type": "range", "bounds": [1e-5, 1e-2], "log_scale": True}],
        objectives={"avg_ep_rew": ObjectiveProperties(minimize=False)},
    )
    _, trial_index = client.get_next_trial()
    client.complete_trial(trial_index=trial_index, raw_data=0.0)
    print("  AxClient: create_experiment(objectives=...), get_next_trial, complete_trial")


# ------------------------------------------------------------------------------
# Main

def main():
    check("Python version", check_python)
    check("PyTorch (CPU)", check_torch)
    check("gymnasium rendering (pygame-ce)", check_gymnasium_render)
    check("OpenCV video", check_opencv_video)
    check("Stable-Baselines3", check_sb3)
    check("Weights & Biases (offline)", check_wandb)
    check("Ax", check_ax)

    if _failures:
        print(f"FAILED: {', '.join(_failures)}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
