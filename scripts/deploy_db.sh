#!/bin/bash

# Configuration
DB_CONTAINER_NAME="price_scrapper-db-1"
BACKEND_CONTAINER_NAME="price_scrapper-backend-ts-1"
DB_USER="user"
DB_NAME="pricedb"
SQL_FILE="backend-ts/prisma/triggers.sql"

echo "🚀 Starting Database Update Process..."

# 1. Update Schema via Prisma
echo "------------------------------------------------"
echo "Step 1: Syncing Schema with Prisma..."
if docker exec $BACKEND_CONTAINER_NAME npx prisma db push; then
    echo "✅ Prisma schema sync complete."
else
    echo "❌ Error: Prisma schema sync failed. Is the container running?"
    exit 1
fi

# 2. Copy and Apply Triggers
echo "------------------------------------------------"
echo "Step 2: Applying Database Triggers..."
if [ -f "$SQL_FILE" ]; then
    # Copy file to container
    docker cp "$SQL_FILE" "$DB_CONTAINER_NAME":/tmp/triggers.sql
    
    # Execute SQL
    docker exec $DB_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /tmp/triggers.sql
    
    echo "✅ Database triggers applied successfully."
else
    echo "❌ Error: $SQL_FILE not found locally."
    exit 1
fi

echo "------------------------------------------------"
echo "🎉 Database is up to date and history tracking is active!"
