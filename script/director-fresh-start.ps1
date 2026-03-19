param(
    [switch]$ClearSettings
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$directorRoot = Join-Path $repoRoot "python_director"
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

$paths = @(
    (Join-Path $directorRoot "pipeline.json"),
    (Join-Path $directorRoot "pipelines"),
    (Join-Path $directorRoot "temp_artifacts"),
    (Join-Path $directorRoot "snapshots"),
    (Join-Path $directorRoot "logs")
)

if ($ClearSettings) {
    $paths += (Join-Path $directorRoot "settings.local.json")
}

foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force
        Write-Host "Removed: $path"
    }
}

@("pipelines", "temp_artifacts", "snapshots", "logs") | ForEach-Object {
    $dir = Join-Path $directorRoot $_
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Set-Content -Path (Join-Path $directorRoot "temp_artifacts\DO_NOT_DELETE") -Value $null -NoNewline

Push-Location $repoRoot
try {
    & $python -c "from python_director.defaults import get_default_pipeline; from python_director.storage import save_pipeline; save_pipeline(get_default_pipeline())"
    Write-Host "Rebuilt default pipeline: $(Join-Path $directorRoot 'pipeline.json')"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Fresh backend state ready."
Write-Host "To clear browser cache too, use Settings > Fresh Start in the UI,"
Write-Host "or run this in browser console on /admin:"
Write-Host "localStorage.removeItem('director_studio_provider_settings_v1');"
Write-Host "localStorage.removeItem('director_studio_ui_activity_log_v1');"
