# Destruction script for Python Director on Google Cloud Run

$PROJECT_ID = "gen-lang-client-0667969294"
$SERVICE_NAME = "director-backend"
$REGION = "us-central1"

Write-Host "WARNING: This will permanently delete the $SERVICE_NAME service on Google Cloud Run." -ForegroundColor Yellow
$confirmation = Read-Host "Are you sure you want to proceed? (y/N)"

if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
    Write-Host "Deleting $SERVICE_NAME..." -ForegroundColor Cyan
    gcloud run services delete $SERVICE_NAME `
        --project $PROJECT_ID `
        --region $REGION `
        --platform managed `
        --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service deleted successfully." -ForegroundColor Green
    } else {
        Write-Host "Failed to delete service." -ForegroundColor Red
    }
} else {
    Write-Host "Operation cancelled."
}
