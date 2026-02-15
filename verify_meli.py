import sys
import os
import logging
from dotenv import load_dotenv

# Config logging
logging.basicConfig(level=logging.INFO)

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

from app.meli_service import get_meli_deals

def verify_mode():
    print("Testing MeliService in 'update_tracked' mode...")
    try:
        alerts, count = get_meli_deals("update_tracked")
        print(f"Processed {count} items.")
        
        if count == 0:
            print("✅ Correctly handled empty database (or no updates needed).")
            print("To add an item, use: python scripts/add_meli_url.py <URL>")
        else:
            print(f"Updated {count} items.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_mode()
