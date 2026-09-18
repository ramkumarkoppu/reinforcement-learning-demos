<#
.SYNOPSIS
    One-time setup of a conda environment that runs these RL demo notebooks natively on Windows.

.DESCRIPTION
    Creates the rl-robotics conda environment (Python 3.12), installs the CPU build of PyTorch plus
    the pinned packages from requirements-native.txt (gymnasium, Stable-Baselines3, pygame-ce,
    Weights & Biases, Ax, JupyterLab), registers the Jupyter kernel "rl-robotics" (shown as
    "Python (RL)") that the notebooks select, and runs verify-native.py.

    Everything the setup needs lives in this folder. Safe to re-run: an existing environment is
    reused and pip only changes what differs, so pointing it at an environment that already has
    some of these packages just adds the rest.

    CPU only is deliberate: the policies in these notebooks are tiny and the simulations run on the
    CPU, so a GPU adds transfer overhead rather than speed. Pass -Gpu for the CUDA build anyway.

.PARAMETER EnvName
    Name of the conda environment. Default: rl-robotics. The notebooks select the kernel of the
    default name; with another name, pick the kernel "Python (RL, <name>)" in JupyterLab yourself.

.PARAMETER TorchVersion
    PyTorch version to install. Default: 2.11.0

.PARAMETER Gpu
    Install the CUDA build of PyTorch instead of the CPU build (needs an NVIDIA driver that
    supports CUDA 13, R580 or newer).

.PARAMETER TorchIndexUrl
    Override the PyTorch wheel index. Default: the CPU index, or the cu130 index with -Gpu.

.PARAMETER SkipVerify
    Do not run verify-native.py at the end.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\windows\setup-native.ps1
#>
param(
    [string]$EnvName = "rl-robotics",
    [string]$TorchVersion = "2.11.0",
    [switch]$Gpu,
    [string]$TorchIndexUrl = "",
    [switch]$SkipVerify
)

# "Continue" on purpose: with "Stop", Windows PowerShell 5.1 can abort on harmless stderr output
# from pip/conda when their output is redirected. Every native command is exit-code checked
# in Invoke-Step instead.
$ErrorActionPreference = "Continue"
. "$PSScriptRoot\common.ps1"

# The PyTorch indexes tag their wheels with a local version label (2.11.0+cpu, 2.11.0+cu130).
# Pinning that label makes pip swap builds when re-running with or without -Gpu; a plain
# "torch==2.11.0" would be reported as already satisfied by either build.
if (-not $TorchIndexUrl) {
    if ($Gpu) {
        $TorchIndexUrl = "https://download.pytorch.org/whl/cu130"
        $TorchSpec = "torch==$TorchVersion+cu130"
    } else {
        $TorchIndexUrl = "https://download.pytorch.org/whl/cpu"
        $TorchSpec = "torch==$TorchVersion+cpu"
    }
} else {
    $TorchSpec = "torch==$TorchVersion"
}

function Invoke-Step {
    param([string]$What, [scriptblock]$Command)
    Write-Host ""
    Write-Host "==> $What" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Step failed ($What), exit code $LASTEXITCODE" }
}

# --- Preconditions -----------------------------------------------------------

$conda = Get-CondaExe
Write-Host "conda:  $conda"

if ($Gpu) {
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        $gpu = (& nvidia-smi --query-gpu=name,driver_version --format=csv,noheader) -join "; "
        Write-Host "GPU:    $gpu"
    } else {
        Write-Warning "-Gpu given but nvidia-smi was not found. PyTorch will fall back to the CPU."
    }
} else {
    Write-Host "Mode:   CPU only (pass -Gpu for the CUDA build of PyTorch)"
}

# --- Conda environment -------------------------------------------------------

$prefix = Get-RlEnvPrefix -EnvName $EnvName
if ($prefix) {
    Write-Host "Reusing existing conda environment: $prefix"
} else {
    Invoke-Step "Creating conda environment '$EnvName' (Python 3.12)" {
        & $conda create -y -n $EnvName python=3.12
    }
    $prefix = Get-RlEnvPrefix -EnvName $EnvName
    if (-not $prefix) { throw "conda environment '$EnvName' was not created" }
}
$py = Join-Path $prefix "python.exe"
Write-Host "python: $py"

# --- Packages ----------------------------------------------------------------

# setuptools is left to pip's resolver: torch pins its own range and upgrading it first only
# produces a conflict warning followed by a downgrade.
Invoke-Step "Upgrading pip and wheel" {
    & $py -m pip install --upgrade pip wheel
}

Invoke-Step "Installing $TorchSpec from $TorchIndexUrl" {
    & $py -m pip install $TorchSpec --index-url $TorchIndexUrl
}

Invoke-Step "Installing gymnasium, Stable-Baselines3, pygame-ce, W&B, Ax, JupyterLab (requirements-native.txt)" {
    & $py -m pip install -r (Join-Path $PSScriptRoot "requirements-native.txt")
}

# The notebooks select the kernel named after the default environment. A custom -EnvName gets its
# own label so two kernels never look identical in the JupyterLab kernel picker.
$kernelLabel = if ($EnvName -eq "rl-robotics") { "Python (RL)" } else { "Python (RL, $EnvName)" }
Invoke-Step "Registering Jupyter kernel '$kernelLabel'" {
    & $py -m ipykernel install --user --name $EnvName --display-name $kernelLabel
}

# --- Verification ------------------------------------------------------------

if (-not $SkipVerify) {
    Invoke-Step "Verifying the installation" {
        & $py (Join-Path $PSScriptRoot "verify-native.py")
    }
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next:  powershell -ExecutionPolicy Bypass -File scripts\windows\start-jupyter.ps1"
