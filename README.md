# Reinforcement Learning Demos

A Jupyter notebook demonstrating reinforcement learning (RL) on the cart pole problem. Open it and execute each of the cells. Note that if you are executing locally, you will need to install [PyTorch](https://pytorch.org/get-started/locally/).

> Running these notebooks locally on Windows instead of Colab? See [Running locally on Windows](#running-locally-on-windows) below. This fork's notebook does not run on Colab; use the [upstream repository](https://github.com/ShawnHymel/reinforcement-learning-demos) for that.

To get started with RL, please watch the [following video](https://www.youtube.com/watch?v=3av8vozEczU):

[![Introduction to Reinforcement Learning YouTube video](https://img.youtube.com/vi/3av8vozEczU/0.jpg)](https://www.youtube.com/watch?v=3av8vozEczU)

The video walks through the [cartpole notebook](rl-demo-cartpole.ipynb), which is the one notebook this fork keeps.

## Running locally on Windows

The notebook in this fork runs in a native Windows conda environment instead of Colab: its `pip install` cell is disabled, it selects the **Python (RL)** Jupyter kernel, and episodes play live in the notebook instead of being recorded to mp4 files with OpenCV. The upstream repository's pendulum, Ax-HPO and Sample Factory demos are not carried here. For Colab, use the upstream repository [ShawnHymel/reinforcement-learning-demos](https://github.com/ShawnHymel/reinforcement-learning-demos).

The setup is self-contained: `scripts\windows\` holds everything it needs, every package is pinned, and re-running it is safe because an existing environment is reused and only what differs is installed.

Prerequisites: [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

One-time setup, run from the root of this clone in PowerShell. It creates (or reuses) the `rl-robotics` environment with Python 3.12, PyTorch (CPU build by default, CUDA with `-Gpu`), gymnasium 1.2.3, Stable-Baselines3 2.9 and JupyterLab, registers the `rl-robotics` Jupyter kernel (shown as **Python (RL)**) that the notebook selects, and verifies everything:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\setup-native.ps1
```

Add `-Gpu` to install the CUDA build of PyTorch instead (`-CudaVersion` selects which, default `cu128`). The two builds share a version number but not a wheel (`2.11.0+cpu` against `2.11.0+cu128`), so re-running the setup without `-Gpu` swaps the CUDA build back out.

Every time you want to work, again from the root of the clone:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\start-jupyter.ps1
```

Then open the notebook and run the cells. Re-check the environment at any time: `conda activate rl-robotics` (in an Anaconda PowerShell Prompt, or after `conda init powershell`) and then `python scripts\windows\verify-native.py` from the root of the clone.

Notes:

 * The first code cell of the notebook keeps the original `pip install` lines as comments. Do not re-enable them: gymnasium 0.28.1 would replace the 1.2.3 the environment is built on, and the old Stable-Baselines3 pin does not install on Python 3.12.
 * Do not install `pygame` or `gymnasium[classic-control]`. Stable-Baselines3 brings `pygame-ce`, which provides the same `pygame` module, and the two overwrite each other's files. `verify-native.py` fails if that has happened.
 * Training runs on the CPU by choice, not because the environment lacks CUDA. Nearly all of the time does go into the network, but as Python and framework overhead per call rather than arithmetic: a gradient step in the cartpole notebook is about 35 MFLOP at batch 32, and `predict()` runs at batch 1. A GPU removes none of that overhead and adds a host transfer per call, so it is no faster for the gradient steps and is slower for the per-step `predict()` calls. Run the setup with `-Gpu` if you want the CUDA build for other work, but note that Stable-Baselines3 defaults to `device="auto"`, which selects CUDA whenever a CUDA build is installed: pass `device='cpu'` explicitly in any notebook you want to keep on the CPU.
 * Episodes are shown in the notebook as they run: a single image updates in place while the printed log grows beneath it. Each rendered episode plays at about 30 frames per second, so watching every test slows a run down; set `RENDER_TESTS = False` in the training cell to train at full speed. Only model checkpoints are written next to the notebook, and they are git-ignored.

## License

All code, unless otherwise noted, is licensed under the Zero-Clause BSD (0BSD) license.

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
