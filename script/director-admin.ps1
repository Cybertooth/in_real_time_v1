param(
    [string]$ServerHost = "0.0.0.0",
    [int]$Port = 8001,
    [switch]$NoReload,
    [string]$LogLevel = "",
    [string]$LogFile = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

if ([string]::IsNullOrWhiteSpace($LogLevel)) {
    $LogLevel = if ([string]::IsNullOrWhiteSpace($env:DIRECTOR_LOG_LEVEL)) { "INFO" } else { $env:DIRECTOR_LOG_LEVEL }
}
if ([string]::IsNullOrWhiteSpace($LogFile)) {
    $LogFile = if ([string]::IsNullOrWhiteSpace($env:DIRECTOR_LOG_FILE)) {
        Join-Path $repoRoot "python_director\logs\director.log"
    } else {
        $env:DIRECTOR_LOG_FILE
    }
}

$env:DIRECTOR_LOG_LEVEL = $LogLevel
$env:DIRECTOR_LOG_FILE = $LogFile

$uvicornArgs = @("-m", "uvicorn", "python_director.api:app", "--host", $ServerHost, "--port", $Port)
if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

# Auto-build React UI if dist/ is missing
$uiDist = Join-Path $repoRoot "python_director\admin_ui_v3\dist"
$uiDir = Join-Path $repoRoot "python_director\admin_ui_v3"
if ((Test-Path $uiDir) -and -not (Test-Path $uiDist)) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        Write-Host "Admin UI not built yet. Building..." -ForegroundColor Cyan
        Push-Location $uiDir
        try {
            & npm install
            & npm run build
            Write-Host "Admin UI built." -ForegroundColor Green
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "WARNING: Admin UI not built and npm not found. Run director-install.ps1 first." -ForegroundColor Yellow
    }
}

Push-Location $repoRoot
try {
    Write-Host "Director Studio starting on http://$ServerHost`:$Port"
    Write-Host "DIRECTOR_LOG_LEVEL=$($env:DIRECTOR_LOG_LEVEL)"
    Write-Host "DIRECTOR_LOG_FILE=$($env:DIRECTOR_LOG_FILE)"
    Write-Host "Logs stream to console and rotate in file."
    & $python @uvicornArgs
}
finally {
    Pop-Location
}
