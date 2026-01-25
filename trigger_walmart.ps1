# Script to manually trigger the Walmart scraping service
# This command runs inside the 'worker' container of the docker-compose setup

Write-Host "🚀 Triggering Walmart Service manual scan..." -ForegroundColor Cyan

# We use 'docker compose exec' to run the command in the running worker container
# we call the scan_walmart_deals function directly for immediate execution
docker compose exec worker python -c "from app.tasks import scan_walmart_deals; scan_walmart_deals()"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Walmart scan task started successfully!" -ForegroundColor Green
    Write-Host "Check the logs using: docker compose logs -f worker" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to trigger Walmart scan." -ForegroundColor Red
}
