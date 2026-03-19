param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    $venvDir = Join-Path $repoRoot ".venv"
    if (-not (Test-Path $venvDir)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        & python -m venv .venv
    }

    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    $python = if (Test-Path $venvPython) { $venvPython } else { "python" }

    Write-Host "Using python: $python" -ForegroundColor Gray
    Write-Host "Installing requirements..." -ForegroundColor Cyan
    & $python -m pip install -r "python_director/requirements.txt" @ExtraArgs
    Write-Host "Installation complete!" -ForegroundColor Green
}
finally {
    Pop-Location
}
