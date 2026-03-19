param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

$reloadArg = if ($NoReload) { @() } else { @("--reload") }

Push-Location $repoRoot
try {
    & $python -m uvicorn python_director.api:app --host $Host --port $Port @reloadArg
}
finally {
    Pop-Location
}
