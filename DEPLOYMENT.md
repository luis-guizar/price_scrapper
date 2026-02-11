# Deployment Guide

Follow these steps to deploy your Price Tracker to your Linux server.

## 1. Prerequisites
Ensure your server has **Docker** and **Docker Compose** installed.

## 2. Transfer Code
You can use **Git** (recommended) or `scp` to get your code onto the server.

### Option A: Using Git
1.  Push your local code to a repository (GitHub/GitLab).
2.  On your server:
    ```bash
    git clone https://github.com/your-username/price_tracker.git
    cd price_tracker
    ```

### Option B: Using SCP (Copy files directly)
Run this from your local machine:
```bash
# Copy project folder to server (excluding venv/node_modules if possible)
scp -r c:\Users\lopez\Documents\price_tracker user@your-server-ip:~/price_tracker
```

## 2.1 Packaging (Zip Method)
If you prefer to zip your files, use this PowerShell command to include only the necessary component (excluding local `node_modules`):
```powershell
Compress-Archive -Path "app", "frontend", "scripts", "Dockerfile", "docker-compose.prod.yaml", "requirements.txt", ".env", "update_schema.py" -DestinationPath "deploy.zip" -Force
```
Then send it:
```bash
scp deploy.zip user@your-server-ip:~
# On server: unzip deploy.zip -d price_tracker
```

## 3. Configure Environment
Create a `.env` file in the project directory on your server to store your secrets.

1.  Create the file:
    ```bash
    nano .env
    ```
2.  Paste the following (fill in your real values):
    ```env
    # Database
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=pricedb

    # Telegram
    TELEGRAM_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_chat_id
    
    # Optional: If you changed port or other settings
    ```
3.  Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

## 4. Start Services
Run Docker Compose to build and start the containers.
```bash
docker compose -f docker-compose.prod.yaml up -d --build
```

## 5. Post-Deployment Setup (Database)
After the containers are running, you must initialize the database schema and backfill existing data.

1. **Update Schema**:
   ```bash
   docker compose -f docker-compose.prod.yaml exec -T worker python update_schema.py
   ```

2. **Backfill Data sources** (Fixes null 'source' fields):
   ```bash
   docker compose -f docker-compose.prod.yaml exec -T worker python scripts/backfill_data.py
   ```

## 6. Access the App & Logs (Self-Hosted Runner)
Since you are using a self-hosted runner, the active application is located in the runner's work directory.

**Location:**
```bash
cd ~/actions-runner/_work/price_scrapper/price_scrapper
```

**View Logs:**
```bash
docker compose -f docker-compose.yaml logs -f worker
```
