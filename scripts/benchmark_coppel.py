import sys
import os
import logging
import time
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.coppel_service import CoppelService

# Configure logging to show info but less verbose for libraries
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("playwright").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

def benchmark_scrape():
    print("🚀 Starting Coppel Service Benchmark...")
    print("=" * 60)
    
    # Load URLs
    urls = []
    try:
        with open("coppel_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)
    except FileNotFoundError:
        print("❌ Error: coppel_urls.txt not found")
        return

    if not urls:
        print("❌ No URLs found to test.")
        return

    # Select a subset of URLs for testing (e.g., first 3 to test parallelism across categories too)
    test_urls = urls[:3]
    print(f"📋 Testing with {len(test_urls)} URLs:")
    for u in test_urls:
        print(f"  - {u}")
    print("=" * 60)

    start_time = time.time()
    
    service = CoppelService(test_urls)
    try:
        # Run the updated service
        products = service.run()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("✅ Benchmark Complete!")
        print("=" * 60)
        print(f"⏱️  Total Duration:   {duration:.2f} seconds")
        print(f"📦 Products Found:   {len(products)}")
        if duration > 0:
            print(f"⚡ Speed:            {len(products) / duration:.2f} products/sec")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Benchmark Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    benchmark_scrape()
