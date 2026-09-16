# Reinforcement Learning Demos

A collection of Jupyter Notebook scripts used to demonstrate reinforcement learning (RL). Open each notebook (either locally or with Google Colab) and execute each of the cells. Note that if you are executing locally, you will need to install [PyTorch](https://pytorch.org/get-started/locally/).

> Running these notebooks locally on Windows instead of Colab? See [Running locally on Windows](#running-locally-on-windows) below. This branch does not run on Colab; use upstream `main` for that.

To get started with RL, please watch the [following video](https://www.youtube.com/watch?v=3av8vozEczU):

[![Introduction to Reinforcement Learning YouTube video](https://img.youtube.com/vi/3av8vozEczU/0.jpg)](https://www.youtube.com/watch?v=3av8vozEczU)

The video walks through the [cartpole notebook](rl-demo-cartpole.ipynb). At the end, viewers are encouraged to modify that notebook to solve the [inverted pendulum problem](https://gymnasium.farama.org/environments/classic_control/pendulum/). I highly recommend trying this on your own before looking at my solution in the [pendulum notebook](rl-demo-pendulum.ipynb).

A discussion of the pendulum solution can be found here %%%LINK%%%.

## Running locally on Windows

The notebooks on this branch (`rl-robotics-windows`) run in a native Windows conda environment instead of Colab: their `pip install` cells are disabled, they select the **Python (RL)** Jupyter kernel, and `rl-demo-pendulum-ax-hpo.ipynb` carries two small edits for Ax 1.3 (the removed `ax.utils.tutorials.cnn_utils` import is gone, and `create_experiment()` takes `objectives={...: ObjectiveProperties(minimize=False)}` instead of the removed `objective_name=` and `minimize=` keywords). For Colab, use upstream `main`.

The environment is the same `rl-robotics` environment that [workshop-reinforcement-learning-for-robotics](https://github.com/ramkumarkoppu/workshop-reinforcement-learning-for-robotics) uses, with identical package pins, so either repository's setup script can run first and each only adds what is missing. This repository's copy is self-contained.

Prerequisites: [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

One-time setup, run from the root of this clone in PowerShell. It creates (or reuses) the `rl-robotics` environment with Python 3.12, PyTorch CPU, gymnasium 1.2.3, Stable-Baselines3 2.9, OpenCV 5, wandb 0.30, Ax 1.3.1 and JupyterLab, registers the `rl-robotics` Jupyter kernel (shown as **Python (RL)**) that the notebooks select, and verifies everything:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\setup-native.ps1
```

Every time you want to work, again from the root of the clone:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\start-jupyter.ps1
```

Then open a notebook and run the cells. Re-check the environment at any time: `conda activate rl-robotics` (in an Anaconda PowerShell Prompt, or after `conda init powershell`) and then `python scripts\windows\verify-native.py` from the root of the clone.

Notes:

 * The first code cell of each notebook keeps the original `pip install` lines as comments. Do not re-enable them: gymnasium 0.28.1 would replace the 1.2.3 the environment is built on, the old Stable-Baselines3 and wandb pins do not install on Python 3.12, and ax-platform 0.3.4 installs but cannot be imported with numpy 2 and predates the `objectives=` API the HPO notebook now uses.
 * Do not install `pygame` or `gymnasium[classic-control]`. Stable-Baselines3 brings `pygame-ce`, which provides the same `pygame` module, and the two overwrite each other's files. `verify-native.py` fails if that has happened.
 * Do not upgrade `ax-platform` past 1.3.x. Ax 1.3 deprecates `AxClient`, which the HPO notebook is built on, and announces its removal in 1.4.0; the DeprecationWarning the notebook prints is expected.
 * `rl-demo-pendulum-ax-hpo.ipynb` reads each trial's results back from the Weights & Biases cloud (`wandb.Api()`), so it needs internet access and `wandb login`.
 * Training is CPU only; run the setup with `-Gpu` for the CUDA build of PyTorch. The networks here are small enough that the CPU is not the bottleneck.
 * `sample-factory/` and `rl-demo-pendulum-sf.ipynb` are not part of this setup. Sample Factory 2.1.1 requires numpy < 2 and gymnasium < 1, older releases need the unmaintained `gym` package, and the project has no Windows support. `sf-test-01.ipynb` also has a syntax error as checked in.
 * The notebooks write videos and model checkpoints next to themselves; those are git-ignored, except `1-random.mp4`, which upstream tracks and which gets overwritten (`git checkout -- 1-random.mp4` restores it).

## License

All code, unless otherwise noted, is licensed under the Zero-Clause BSD (0BSD) license.

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
