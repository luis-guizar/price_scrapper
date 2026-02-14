import requests
import logging
import time
import math
import concurrent.futures
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product, PriceHistory

# Configurar logging
logger = logging.getLogger(__name__)

class CyberpuertaScraper:
    def __init__(self, filter_urls):
        self.filter_urls = filter_urls
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.cyberpuerta.mx/"
        })
        self.collected_ids = []
        self.products = []

    def discover_ids(self):
        """Step 1: Dynamic Discovery (Index Phase)"""
        logger.info(f"🔍 Starting discovery phase for {len(self.filter_urls)} filter URLs.")
        
        for url in self.filter_urls:
            try:
                # Initial call to get pagination info
                logger.info(f"Checking filter URL: {url}")
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                total_pages = data.get("data", {}).get("totalPages", 0)
                total_items = data.get("data", {}).get("total", 0)
                
                if not total_pages or total_pages == 0:
                    logger.warning(f"No pages found for {url}")
                    continue
                    
                logger.info(f"Found {total_items} items across {total_pages} pages.")
                
                # Pagination Loop
                # Note: Assuming 'page' parameter in URL can be replaced or appended. 
                # The provided example URL has &page=1. We'll handle this by parsing or replacing.
                base_url = url
                if "page=" in base_url:
                    # Remove existing page param to append cleanly in loop, or just replace
                    # Simple strategy: use regex or string replacement if we know the format
                    pass 
                
                for page in range(1, total_pages + 1):
                    # Construct URL for specific page
                    # If URL already has page=1, replace it. 
                    # If not, append it. 
                    if "page=" in base_url:
                        page_url = base_url.replace(f"page=1", f"page={page}") # Simple replacement for now if starts with 1
                        # If the original URL had page=XY, this simple replace might fail if not page=1 initially.
                        # A more robust way:
                        import re
                        page_url = re.sub(r'page=\d+', f'page={page}', base_url)
                    else:
                        page_url = f"{base_url}&page={page}"
                    
                    logger.debug(f"Scanning page {page}/{total_pages}...")
                    
                    try:
                        resp = self.session.get(page_url)
                        resp.raise_for_status()
                        page_data = resp.json()
                        
                        article_ids = page_data.get("data", {}).get("articleIds", [])
                        self.collected_ids.extend(article_ids)
                        
                        time.sleep(1) # Resilience: 1-second delay
                        
                    except Exception as e:
                        logger.error(f"Error fetching page {page}: {e}")
                        
            except Exception as e:
                logger.error(f"Error initializing discovery for {url}: {e}")
        
        # Deduplicate IDs
        self.collected_ids = list(set(self.collected_ids))
        logger.info(f"✅ Discovery complete. Collected {len(self.collected_ids)} unique IDs.")

    def fetch_details(self):
        """Step 2: Batch Hydration (Detail Phase)"""
        if not self.collected_ids:
            logger.warning("No IDs to fetch.")
            return

        chunk_size = 24
        chunks = [self.collected_ids[i:i + chunk_size] for i in range(0, len(self.collected_ids), chunk_size)]
        
        logger.info(f"Hydrating {len(self.collected_ids)} products in {len(chunks)} batches.")
        
        url = "https://api.cyberpuerta.mx/v2/catalog/articles"
        
        def process_chunk(chunk_ids):
            try:
                # requests.get params handles list as key=value&key=value if passed as list of tuples or similar
                # But example shows articles[]=ID
                # requests supports key w/ [] if we construct it right or pass dict with list
                
                params = [('articles[]', pid) for pid in chunk_ids]
                
                resp = self.session.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
                # Extract product data from response
                # Structure needs verification, assuming data -> returned articles
                # Based on typical API: data might be a dict or list
                
                # Let's assume the response 'data' contains the articles directly or inside a key
                # Looking at typical cyberpuerta responses or inferring:
                # usually { "data": { "123": { ... }, "456": { ... } } } or list
                # For now, we'll assume 'data' holds the map or list.
                
                items = data.get("data", {})
                processed_items = []
                
                # If items is a dict keyed by ID
                if isinstance(items, dict):
                    processed_items = items.values()
                elif isinstance(items, list):
                    processed_items = items
                
                results = []
                for item in processed_items:
                    # Normalize data
                    # Need: name, price, url, sku/id, image
                    
                    # Extract fields (Guessing typical fields, adjusting based on debugging if needed)
                    pid = str(item.get("articleId", "")) or str(item.get("id", ""))
                    title = item.get("title", "") or item.get("name", "")
                    price = float(item.get("price", 0))
                    
                    # URL construction if not provided
                    # Cyberpuerta usually has 'url' or 'slug'
                    slug = item.get("slug", "")
                    product_url = item.get("url", "")
                    if not product_url and slug:
                        product_url = f"https://www.cyberpuerta.mx/{slug}" # Guessing base
                    
                    image = item.get("image", "") or item.get("picture", "")
                    
                    if pid and title and price > 0:
                        results.append({
                            "name": title,
                            "sku": pid,
                            "url": product_url,
                            "price": price,
                            "image": image,
                            "source": "cyberpuerta"
                        })
                return results

            except Exception as e:
                logger.error(f"Error fetching batch: {e}")
                return []

        # Use ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                batch_results = future.result()
                self.products.extend(batch_results)
                
        logger.info(f"✅ Details fetched. Total products: {len(self.products)}")

    def run(self):
        self.discover_ids()
        self.fetch_details()
        return self.products

def process_products(products, db_session: Session):
    """
    Save products to DB and check for alerts.
    """
    alerts = []
    processed_count = 0
    
    # Configuration for alerts (hardcoded or from config)
    MIN_DROP_PCT = 20
    MIN_DROP_AMOUNT = 500
    
    for p in products:
        try:
            sku = p['sku']
            url = p['url']
            price = p['price']
            name = p['name']
            
            # Find existing product
            # Prefer SKU match for Cyberpuerta as URL might change or be constructed
            db_product = db_session.query(Product).filter(Product.sku == sku).first()
            
            if not db_product:
                # Try URL
                db_product = db_session.query(Product).filter(Product.url == url).first()
            
            if db_product:
                # Existing product
                old_price = db_product.current_price
                
                # Check for price drop
                if price < old_price:
                    drop = old_price - price
                    pct = (drop / old_price) * 100
                    
                    if pct >= MIN_DROP_PCT or drop >= MIN_DROP_AMOUNT:
                        alerts.append({
                            "source": "cyberpuerta",
                            "title": name,
                            "price": price,
                            "old_price": old_price,
                            "discount_pct": round(pct, 1),
                            "url": url,
                            "sku": sku
                        })
                
                # Update price if changed
                if abs(price - old_price) > 0.1:
                    db_product.current_price = price
                    history = PriceHistory(product=db_product, price=price)
                    db_session.add(history)
                
                db_product.last_checked = datetime.utcnow()
                db_product.url = url # Update URL just in case
                
            else:
                # New Product
                new_prod = Product(
                    name=name,
                    sku=sku,
                    url=url,
                    current_price=price,
                    source="cyberpuerta",
                    last_checked=datetime.utcnow()
                )
                db_session.add(new_prod)
                # Flush to get ID for history
                db_session.flush()
                
                history = PriceHistory(product=new_prod, price=price)
                db_session.add(history)
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing product {p.get('sku')}: {e}")
            continue
            
    try:
        db_session.commit()
    except Exception as e:
        logger.error(f"DB Commit error: {e}")
        db_session.rollback()
        
    return alerts, processed_count

def get_cyberpuerta_deals():
    # Read URLs from file or config
    # For now, using the one requested or a default list
    # In a real scenario, this might come from a DB or config file
    
    # Load URLs from local file if exists, otherwise empty
    filter_urls = []
    try:
        with open("cyberpuerta_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "filter?id=" in line:
                    filter_urls.append(line)
    except FileNotFoundError:
        logger.warning("cyberpuerta_urls.txt not found.")
    
    if not filter_urls:
        return [], 0

    scraper = CyberpuertaScraper(filter_urls)
    products = scraper.run()
    
    session = SessionLocal()
    try:
        alerts, count = process_products(products, session)
        return alerts, count
    finally:
        session.close()
