import sys
import os
import requests
import json
import logging
from dotenv import load_dotenv

# Config logging
logging.basicConfig(level=logging.INFO)

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

from app.meli_service import MeliService

def verify_meli_auth():
    print("Initializing MeliService (checking Redis tokens)...")
    service = MeliService()
    
    token = service.access_token
    print(f"Current Access Token (partial): {token[:10]}...{token[-10:] if token else 'None'}")
    
    if not token:
        print("❌ No access token found in MeliService!")
        return

    headers = {"Authorization": f"Bearer {token}"}
    print("Testing /users/me...")
    try:
        response = requests.get("https://api.mercadolibre.com/users/me", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Authentication Valid!")
            user_data = response.json()
            print(f"User ID: {user_data.get('id')}")
            print(f"Nickname: {user_data.get('nickname')}")
            print(f"Email: {user_data.get('email')}")
        else:
            print(f"❌ Authentication Failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during request: {e}")

if __name__ == "__main__":
    verify_meli_auth()
