param(
    [Parameter(Mandatory = $true)]
    [string]$Message
)

# Wrapper to run the python update sender
Write-Host "🚀 Sending update to Telegram Group..." -ForegroundColor Cyan

# Run the python script
python send_update.py "$Message"

if ($LASTEXITCODE -eq 0) {
    # The python script handles its own success message, but we can add a wrapper status if needed.
    # Write-Host "Update sent." -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to run update script." -ForegroundColor Red
}
