# Configuration
$DB_CONTAINER = "price_scrapper-db-1"
$BACKEND_CONTAINER = "price_scrapper-backend-ts-1"
$DB_USER = "user"
$DB_NAME = "pricedb"
$SQL_FILE = "backend-ts/prisma/triggers.sql"

Write-Host "🚀 Starting Database Update Process..." -ForegroundColor Cyan

# 1. Update Schema via Prisma
Write-Host "------------------------------------------------"
Write-Host "Step 1: Syncing Schema with Prisma..."
docker exec $BACKEND_CONTAINER npx prisma db push
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Prisma schema sync complete." -ForegroundColor Green
}
else {
    Write-Host "❌ Error: Prisma schema sync failed. Is the container running?" -ForegroundColor Red
    exit
}

# 2. Copy and Apply Triggers
Write-Host "------------------------------------------------"
Write-Host "Step 2: Applying Database Triggers..."
if (Test-Path $SQL_FILE) {
    # Copy file to container
    docker cp $SQL_FILE "${DB_CONTAINER}:/tmp/triggers.sql"
    
    # Execute SQL
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /tmp/triggers.sql
    
    Write-Host "✅ Database triggers applied successfully." -ForegroundColor Green
}
else {
    Write-Host "❌ Error: $SQL_FILE not found locally." -ForegroundColor Red
    exit
}

Write-Host "------------------------------------------------"
Write-Host "🎉 Database is up to date and history tracking is active!" -ForegroundColor Cyan
