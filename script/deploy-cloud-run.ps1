# Deployment script for Python Director to Google Cloud Run

$PROJECT_ID = "gen-lang-client-0667969294"
$SERVICE_NAME = "director-backend"
$REGION = "us-central1"
$ARTIFACT_BUCKET = "$PROJECT_ID-artifacts"

Write-Host "Deploying $SERVICE_NAME to Google Cloud Run in project $PROJECT_ID ($REGION)..." -ForegroundColor Cyan

# Navigate to the python_director directory
Push-Location "$PSScriptRoot\..\python_director"

$ENV_FILE = ".env"
$SCHEDULER_SHARED_SECRET = $null

if (Test-Path $ENV_FILE) {
    $content = Get-Content $ENV_FILE
    $secretLine = $content | Where-Object { $_ -match "^SCHEDULER_SHARED_SECRET=(.*)" }
    if ($secretLine) {
        $SCHEDULER_SHARED_SECRET = $matches[1].Trim()
    }
}

if (-not $SCHEDULER_SHARED_SECRET) {
    Write-Host "Generating new SCHEDULER_SHARED_SECRET..." -ForegroundColor Yellow
    $bytes = New-Object byte[] 16
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $SCHEDULER_SHARED_SECRET = -join ($bytes | ForEach-Object { "{0:x2}" -f $_ })
    Add-Content -Path $ENV_FILE -Value "`nSCHEDULER_SHARED_SECRET=$SCHEDULER_SHARED_SECRET"
    Write-Host "Saved new secret to .env file." -ForegroundColor Green
}

try {
    # Run the deployment command with GCS volume mount for durable storage
    gcloud run deploy $SERVICE_NAME `
        --source . `
        --project $PROJECT_ID `
        --region $REGION `
        --allow-unauthenticated `
        --update-env-vars="SCHEDULER_SHARED_SECRET=$SCHEDULER_SHARED_SECRET" `
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
            --headers="Authorization=Bearer $SCHEDULER_SHARED_SECRET" `
            --location=$REGION `
            --project=$PROJECT_ID
        Write-Host "Created Cloud Scheduler job." -ForegroundColor Green
    } else {
        gcloud scheduler jobs update http $SCHEDULER_JOB_NAME `
            --schedule="0 * * * *" `
            --uri="$URL/api/scheduler/tick" `
            --http-method="POST" `
            --headers="Authorization=Bearer $SCHEDULER_SHARED_SECRET" `
            --location=$REGION `
            --project=$PROJECT_ID
        Write-Host "Updated Cloud Scheduler job." -ForegroundColor Green
    }

} else {
    Write-Host "`nDeployment failed." -ForegroundColor Red
}
