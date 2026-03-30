# Deployment script for Python Director to Google Cloud Run

$PROJECT_ID = "gen-lang-client-0667969294"
$SERVICE_NAME = "director-backend"
$REGION = "us-central1"
$ARTIFACT_BUCKET = "$PROJECT_ID-artifacts"

Write-Host "Deploying $SERVICE_NAME to Google Cloud Run in project $PROJECT_ID ($REGION)..." -ForegroundColor Cyan

# Navigate to the python_director directory
Push-Location "$PSScriptRoot\..\python_director"

try {
    # Run the deployment command with GCS volume mount for durable storage
    gcloud run deploy $SERVICE_NAME `
        --source . `
        --project $PROJECT_ID `
        --region $REGION `
        --allow-unauthenticated `
        --add-volume="name=artifacts,type=cloud-storage,bucket=$ARTIFACT_BUCKET" `
        --add-volume-mount="volume=artifacts,mount-path=/app/temp_artifacts"
}
finally {
    Pop-Location
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDeployment successful!" -ForegroundColor Green
    $URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID
    Write-Host "Service URL: $URL" -ForegroundColor White
    
    # Configure scheduler job
    $SCHEDULER_JOB_NAME = "director-auto-deploy-tick"
    Write-Host "Configuring Cloud Scheduler job '$SCHEDULER_JOB_NAME'..." -ForegroundColor Cyan
    
    # Check if job exists
    $jobExists = gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location $REGION --project $PROJECT_ID 2>$null
    
    if (-not $jobExists) {
        gcloud scheduler jobs create http $SCHEDULER_JOB_NAME `
            --schedule="0 * * * *" `
            --uri="$URL/api/scheduler/tick" `
            --http-method="POST" `
            --location=$REGION `
            --project=$PROJECT_ID
        Write-Host "Created Cloud Scheduler job." -ForegroundColor Green
    } else {
        gcloud scheduler jobs update http $SCHEDULER_JOB_NAME `
            --schedule="0 * * * *" `
            --uri="$URL/api/scheduler/tick" `
            --http-method="POST" `
            --location=$REGION `
            --project=$PROJECT_ID
        Write-Host "Updated Cloud Scheduler job." -ForegroundColor Green
    }

} else {
    Write-Host "`nDeployment failed." -ForegroundColor Red
}
