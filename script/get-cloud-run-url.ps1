# Script to retrieve the current Cloud Run URL for Python Director

$PROJECT_ID = "gen-lang-client-0667969294"
$SERVICE_NAME = "python-director"
$REGION = "us-central1"

$URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID

if ($URL) {
    Write-Host "Current Backend URL: " -NoNewline
    Write-Host $URL -ForegroundColor Green
    Write-Host "`nCopy this URL to your Flutter app's Settings screen."
} else {
    Write-Host "Could not retrieve service URL. Is the service deployed?" -ForegroundColor Red
}
