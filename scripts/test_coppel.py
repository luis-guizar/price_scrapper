import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.coppel_service import CoppelService

logging.basicConfig(level=logging.INFO)

def test_final():
    print("Testing CoppelService (Final Verification)...")
    
    # Load URLs from file
    urls = []
    try:
        with open("coppel_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)
        print(f"Loaded {len(urls)} URLs from coppel_urls.txt")
    except FileNotFoundError:
        print("❌ Error: coppel_urls.txt not found")
        return

    service = CoppelService(urls)
    try:
        products = service.run()
        print(f"✅ Found {len(products)} products.")
        if products:
            print("Sample Product:")
            print(f"  Name: {products[0]['name']}")
            print(f"  Price: {products[0]['price']}")
            print(f"  URL: {products[0]['url']}")
    except Exception as e:
        print(f"❌ Error running service: {e}")

if __name__ == "__main__":
    test_final()
