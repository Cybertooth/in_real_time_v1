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
    Write-Host "Installing Python requirements..." -ForegroundColor Cyan
    & $python -m pip install -r "python_director/requirements.txt" @ExtraArgs

    # Build React admin UI
    $uiDir = Join-Path $repoRoot "python_director\admin_ui_v3"
    if (Test-Path $uiDir) {
        $npm = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $npm) {
            Write-Host "WARNING: npm not found. Install Node.js (>=18) to build the admin UI." -ForegroundColor Yellow
        } else {
            Write-Host "Installing admin UI dependencies..." -ForegroundColor Cyan
            Push-Location $uiDir
            try {
                & npm install
                Write-Host "Building admin UI..." -ForegroundColor Cyan
                & npm run build
                Write-Host "Admin UI built successfully." -ForegroundColor Green
            } finally {
                Pop-Location
            }
        }
    }

    Write-Host "Installation complete!" -ForegroundColor Green
}
finally {
    Pop-Location
}
