# Shared helpers for the native Windows scripts. Dot-source this file:
#     . "$PSScriptRoot\common.ps1"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Get-CondaExe {
    # Prefer the conda.exe on PATH, then the usual Anaconda/Miniconda install locations, and as a
    # last resort the "conda" shell function that "conda init powershell" installs.
    $app = Get-Command conda.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandType -eq "Application" } | Select-Object -First 1
    if ($app) { return $app.Source }
    $candidates = @(
        "$env:ProgramData\anaconda3\Scripts\conda.exe",
        "$env:ProgramData\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:LOCALAPPDATA\anaconda3\Scripts\conda.exe",
        "$env:LOCALAPPDATA\miniconda3\Scripts\conda.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    if (Get-Command conda -ErrorAction SilentlyContinue) { return "conda" }
    throw "conda was not found. Install Anaconda or Miniconda, or add conda to PATH."
}

function Get-RlEnvPrefix {
    param([string]$EnvName = "rl-robotics")
    # Fast path: the default per-user envs directory.
    $default = Join-Path $env:USERPROFILE ".conda\envs\$EnvName"
    if (Test-Path (Join-Path $default "python.exe")) { return $default }
    # Otherwise ask conda where its environments live.
    $conda = Get-CondaExe
    $info = & $conda env list --json | ConvertFrom-Json
    foreach ($p in $info.envs) {
        if ((Split-Path $p -Leaf) -eq $EnvName) { return $p }
    }
    return $null
}

function Get-RlPython {
    param([string]$EnvName = "rl-robotics")
    $prefix = Get-RlEnvPrefix -EnvName $EnvName
    if (-not $prefix) {
        throw "conda environment '$EnvName' not found. Run scripts\windows\setup-native.ps1 first."
    }
    return (Join-Path $prefix "python.exe")
}
