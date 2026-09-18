"""
Verify the native Windows environment for this RL demo notebook.

Run with the rl-robotics conda environment's Python, e.g.:

    conda activate rl-robotics
    python scripts/windows/verify-native.py

Checks Python, PyTorch (either build), gymnasium rendering through pygame-ce, the notebook's
inline frame display and Stable-Baselines3. Exit code is 0 when every check passes, 1 otherwise.
"""

import importlib.metadata
import io
import math
import os
import sys
import tempfile
import time
import traceback

# Non-ASCII output (progress marks, warnings) raises UnicodeEncodeError under the cp1252 console
# encoding as soon as the output is redirected to a file or a pipe.
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

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
        print(f"  CUDA build; {torch.cuda.get_device_name(0)} visible")
        print("  SB3 defaults to device='auto' (CUDA); device='cpu' notebooks unaffected")
    else:
        print("  CPU build (run setup-native.ps1 -Gpu for the CUDA build)")


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

    # The notebook renders off-screen (render_mode="rgb_array") and shows the frames inline
    env = gym.make("CartPole-v1", render_mode="rgb_array")
    env.reset(seed=0)
    frame = env.render()
    assert frame.shape == (400, 600, 3), f"CartPole-v1: unexpected frame shape {frame.shape}"
    env.step(env.action_space.sample())
    env.close()
    print("  CartPole-v1 rendered off-screen through pygame")


def check_inline_render():
    """The notebook captions each frame with Pillow and displays it through IPython."""
    import numpy as np
    import PIL
    from IPython.display import display
    from PIL import Image, ImageDraw, ImageFont
    print(f"  pillow {PIL.__version__}")

    frame = np.zeros((500, 500, 3), dtype=np.uint8)
    img = Image.fromarray(frame)
    ImageDraw.Draw(img).text((10, 10), "verify", fill=(255, 255, 255), font=ImageFont.load_default(size=20))
    assert np.array(img).max() > 0, "caption was not drawn onto the frame"

    # display() is what puts the frame in the notebook; outside one it has no frontend to draw on,
    # so check the PNG encoding it would send instead.
    png = img._repr_png_()
    assert png[:8] == b"\x89PNG\r\n\x1a\n", "frame did not encode as PNG"
    assert Image.open(io.BytesIO(png)).size == (500, 500)
    assert callable(display)
    print(f"  captioned frame -> {len(png)} byte PNG for display() in the notebook")


def check_sb3():
    import gymnasium as gym
    import stable_baselines3 as sb3
    print(f"  stable-baselines3 {sb3.__version__}")
    with tempfile.TemporaryDirectory() as d:
        # DQN on CartPole as in rl-demo-cartpole.ipynb. device="cpu" keeps the check off the GPU
        # when the CUDA build is installed; SB3 would otherwise default to "auto", i.e. CUDA.
        env = gym.make("CartPole-v1")
        dqn = sb3.DQN("MlpPolicy", env, learning_starts=32, train_freq=8, verbose=0, device="cpu")
        dqn.learn(total_timesteps=64)
        dqn.save(os.path.join(d, "dqn"))
        sb3.DQN.load(os.path.join(d, "dqn"), device="cpu")
        env.close()
    print("  DQN: learn, save, load with device='cpu'")


# ------------------------------------------------------------------------------
# Main

def main():
    check("Python version", check_python)
    check("PyTorch", check_torch)
    check("gymnasium rendering (pygame-ce)", check_gymnasium_render)
    check("Inline frame display (Pillow)", check_inline_render)
    check("Stable-Baselines3", check_sb3)

    if _failures:
        print(f"FAILED: {', '.join(_failures)}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
