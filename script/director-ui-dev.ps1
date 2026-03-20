param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$uiDir = Join-Path $repoRoot "python_director\admin_ui_v3"

if (-not (Test-Path $uiDir)) {
    Write-Host "ERROR: Admin UI directory not found at $uiDir" -ForegroundColor Red
    exit 1
}

$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host "ERROR: npm not found. Install Node.js (>=18)." -ForegroundColor Red
    exit 1
}

Push-Location $uiDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing dependencies..." -ForegroundColor Cyan
        & npm install
    }
    Write-Host "Starting Vite dev server on http://localhost:$Port" -ForegroundColor Cyan
    Write-Host "API requests proxy to http://localhost:8001" -ForegroundColor Gray
    & npx vite --port $Port
} finally {
    Pop-Location
}
