---
description: How to deploy the Price Tracker to Oracle Cloud (Always Free)
---

This workflow guides you through deploying your Dockerized price tracker to an Oracle Cloud VM.

### 1. Prepare Oracle Cloud Instance
1. Log in to [Oracle Cloud Console](https://cloud.oracle.com/).
2. Go to **Compute** -> **Instances** -> **Create Instance**.
3. **Choose Image:** Use the default **Canonical Ubuntu** (22.04 or 24.04).
4. **Shape:** 
   - Choose **VM.Standard.E2.1.Micro** (x86_64) or **VM.Standard.A1.Flex** (ARM/Ampere) for the "Always Free" tier.
5. **Networking:** Ensure a Public IP is assigned.
6. **SSH Keys:** Save your Private Key (`.key` or `.pem`) to your local machine.

### 2. Connect to your Instance
Open terminal (PowerShell or Bash) and run:
```bash
ssh -i /path/to/your/private_key.key ubuntu@YOUR_INSTANCE_IP
```

### 3. Install Docker & Docker Compose
Once inside the VM, run the following commands:
// turbo
```bash
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
# Log out and log back in for group changes to take effect
exit
```
*Reconnect after exit.*

### 4. Transfer Code
You can use Git (recommended) or SCP.

**Using Git:**
1. Create a repository on GitHub/GitLab and push your local code there.
2. In the VM:
```bash
git clone https://github.com/yourusername/price_tracker.git
cd price_tracker
```

**Using SCP (Direct transfer):**
// turbo
```powershell
# Run this from your LOCAL power-shell
scp -r -i "C:\path\to\key.pem" "C:\Users\lopez\Documents\price_tracker" ubuntu@YOUR_INSTANCE_IP:~/
```

### 5. Setup Environment Variables
In the VM, create the `.env` file:
```bash
nano .env
```
Paste your secrets:
```env
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
```
Press `Ctrl+O`, `Enter`, `Ctrl+X` to save.

### 6. Launch Application
// turbo
```bash
docker-compose up -d --build
```

### 7. Monitor Logs
```bash
docker-compose logs -f worker
```
