<#
.SYNOPSIS
    Start JupyterLab from the rl-robotics environment with this repository as its root.

.DESCRIPTION
    Opens JupyterLab in your browser. Open any rl-demo-*.ipynb; the notebooks already select the
    "Python (RL)" kernel that setup-native.ps1 registered. Ctrl+C in this window stops JupyterLab.

.PARAMETER EnvName
    Name of the conda environment. Default: rl-robotics

.PARAMETER Port
    JupyterLab port. Default: 8888

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\windows\start-jupyter.ps1
#>
param(
    [string]$EnvName = "rl-robotics",
    [int]$Port = 8888
)

# JupyterLab logs to stderr; "Stop" would turn that into errors when output is redirected.
$ErrorActionPreference = "Continue"
. "$PSScriptRoot\common.ps1"

$py = Get-RlPython -EnvName $EnvName

Write-Host "JupyterLab root: $RepoRoot"
Write-Host "Open one of the rl-demo-*.ipynb notebooks; they use the 'Python (RL)' kernel."
& $py -m jupyterlab --notebook-dir="$RepoRoot" --port $Port
