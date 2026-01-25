#!/bin/bash
# Script to manually trigger the Walmart scraping service
# This command runs inside the 'worker' container of the docker-compose setup

echo "🚀 Triggering Walmart Service manual scan..."

# We use 'docker compose exec' to run the command in the running worker container
docker compose exec worker python -c "from app.tasks import scan_walmart_deals; scan_walmart_deals()"

if [ $? -eq 0 ]; then
    echo "✅ Walmart scan task started successfully!"
    echo "Check the logs using: docker compose logs -f worker"
else
    echo "❌ Failed to trigger Walmart scan."
fi
