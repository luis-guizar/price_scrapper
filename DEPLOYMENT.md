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
Compress-Archive -Path "app", "frontend", "Dockerfile", "docker-compose.yaml", "requirements.txt", ".env", "update_schema.py", "send_update.py", "DEPLOYMENT.md", ".dockerignore" -DestinationPath "deploy.zip" -Force
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
docker compose up -d --build
```

## 5. Update Database Schema (CRITICAL)
Once the containers are running, you must apply the schema changes (adding the `source` column and `price_history` table) to your server's database.

Run this command:
```bash
docker compose exec -T worker python update_schema.py
```

You should see logs indicating success:
> ✅ Columna 'source' verificada/agregada CORRECTAMENTE.
> ✅ Tabla 'price_history' verificada/creada.

## 6. Access the App
- **Frontend**: http://your-server-ip:3000
- **Adminer (DB UI)**: http://your-server-ip:8080
- **API Docs**: http://your-server-ip:8001/docs
