import sys
import os
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

# Config logging
logging.basicConfig(level=logging.INFO)

# Load env vars
load_dotenv()

from app.meli_service import get_meli_deals, MeliService

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/add_meli_url.py <URL>")
        return

    url = sys.argv[1]
    print(f"Adding URL: {url}")
    
    try:
        # get_meli_deals handles adding if URL is passed
        alerts, count = get_meli_deals(url)
        print(f"✅ Processed {count} item(s).")
        if count > 0:
            print("Item added/updated in database successfully.")
        else:
            print("❌ Failed to add item. Check URL or logs.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
