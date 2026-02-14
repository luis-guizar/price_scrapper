import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.cyberpuerta_service import CyberpuertaScraper, process_products
from app.models import SessionLocal, init_db

# Configure logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scraper():
    logger.info("🚀 Starting Cyberpuerta Scraper Test")
    
    # Read URLs
    filter_urls = []
    url_file = "cyberpuerta_urls.txt"
    if os.path.exists(url_file):
        with open(url_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "filter?id=" in line:
                    filter_urls.append(line)
    
    if not filter_urls:
        logger.error("❌ No filter URLs found in cyberpuerta_urls.txt")
        return

    logger.info(f"Loaded {len(filter_urls)} filter URLs.")

    # Initialize Scraper
    scraper = CyberpuertaScraper(filter_urls)
    
    # Step 1: Discovery
    logger.info("--- STEP 1: DISCOVERY ---")
    scraper.discover_ids()
    
    if not scraper.collected_ids:
        logger.error("❌ No IDs discovered. Check network or URL validity.")
        return
        
    logger.info(f"Collected {len(scraper.collected_ids)} IDs.")
    
    # Step 2: Hydration (Details)
    logger.info("--- STEP 2: HYDRATION ---")
    scraper.fetch_details()
    
    if not scraper.products:
        logger.error("❌ No products fetched. Check batch endpoint.")
        return
        
    logger.info(f"Fetched details for {len(scraper.products)} products.")
    
    # Verify Data
    logger.info("--- SAMPLE DATA ---")
    for p in scraper.products[:3]:
        logger.info(f"Product: {p.get('name')} | Price: ${p.get('price')} | SKU: {p.get('sku')}")
        
    # Step 3: DB Integration (Optional check)
    logger.info("--- STEP 3: DB INTEGRATION ---")
    
    # init_db() # Ensure tables exist
    # session = SessionLocal()
    # try:
    #     alerts, count = process_products(scraper.products, session)
    #     logger.info(f"Processed {count} products. Generated {len(alerts)} alerts.")
    # finally:
    #     session.close()

if __name__ == "__main__":
    test_scraper()
