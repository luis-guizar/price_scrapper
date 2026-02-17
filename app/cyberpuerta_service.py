import requests
import logging
import time
import math
import concurrent.futures
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product, PriceHistory

import re

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

    def _discover_single_url(self, url):
        """Discover all product IDs from a single filter URL (all pages)."""
        ids = []
        try:
            logger.info(f"Checking filter URL: {url[:80]}...")
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            total_pages = data.get("data", {}).get("totalPages", 0)
            total_items = data.get("data", {}).get("total", 0)
            
            if not total_pages or total_pages == 0:
                logger.warning(f"No pages found for {url[:80]}")
                return ids
                
            logger.info(f"Found {total_items} items across {total_pages} pages.")
            
            # Extract IDs from page 0 (initial call) response
            initial_ids = data.get("data", {}).get("articleIds", [])
            ids.extend(initial_ids)
            
            # Paginate remaining pages (start from 1 since we already have page 0)
            for page in range(1, total_pages):
                page_url = re.sub(r'page=\d+', f'page={page}', url)
                
                try:
                    resp = self.session.get(page_url)
                    resp.raise_for_status()
                    page_data = resp.json()
                    
                    article_ids = page_data.get("data", {}).get("articleIds", [])
                    ids.extend(article_ids)
                    
                    time.sleep(0.5)  # Rate limit per page
                    
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing discovery for {url[:80]}: {e}")
        
        return ids

    def discover_ids(self):
        """Step 1: Dynamic Discovery (Index Phase) — concurrent across URLs."""
        logger.info(f"🔍 Starting discovery phase for {len(self.filter_urls)} filter URLs.")
        
        all_ids = []
        
        # Process multiple filter URLs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {
                executor.submit(self._discover_single_url, url): url 
                for url in self.filter_urls
            }
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    ids = future.result()
                    all_ids.extend(ids)
                    logger.info(f"  ✓ {len(ids)} IDs from {url[:60]}...")
                except Exception as e:
                    logger.error(f"Discovery thread failed for {url[:60]}: {e}")
        
        # Deduplicate IDs
        self.collected_ids = list(set(all_ids))
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
                params = [('articles[]', pid) for pid in chunk_ids]
                
                resp = self.session.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
                # API returns: { "data": [ { "id": "...", "title": "...", "price": 30355, "link": "https://...", "picture": "https://...", "sku": "ABC-123", ... }, ... ] }
                items = data.get("data", [])
                if isinstance(items, dict):
                    items = list(items.values())
                
                results = []
                for item in items:
                    pid = str(item.get("id", ""))
                    title = item.get("title", "")
                    price = float(item.get("price", 0))
                    product_url = item.get("link", "")
                    image = item.get("picture", "")
                    sku = item.get("sku", "") or pid
                    
                    if pid and title and price > 0 and product_url:
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
    Commits in batches of BATCH_SIZE to limit blast radius on failures.
    """
    alerts = []
    processed_count = 0
    failed_count = 0
    BATCH_SIZE = 50
    
    # Configuration for alerts
    MIN_DROP_PCT = 35
    MIN_DROP_AMOUNT = 5000
    
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i + BATCH_SIZE]
        batch_ok = True
        
        for p in batch:
            try:
                sku = p['sku']
                url = p['url']
                price = p['price']
                name = p['name']
                
                # Skip products without valid URL
                if not url or not url.startswith('http'):
                    continue
                
                # Find existing product
                db_product = db_session.query(Product).filter(Product.sku == sku).first()
                
                if not db_product:
                    db_product = db_session.query(Product).filter(Product.url == url).first()
                
                if db_product:
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
                    
                    db_product.last_checked = datetime.now()
                    db_product.url = url
                    
                else:
                    # New Product
                    new_prod = Product(
                        name=name,
                        sku=sku,
                        url=url,
                        current_price=price,
                        source="cyberpuerta",
                        last_checked=datetime.now()
                    )
                    db_session.add(new_prod)
                    db_session.flush()
                    
                    history = PriceHistory(product=new_prod, price=price)
                    db_session.add(history)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing product {p.get('sku')}: {e}")
                batch_ok = False
                break  # Stop this batch, rollback and continue
        
        # Commit this batch
        try:
            if batch_ok:
                db_session.commit()
            else:
                db_session.rollback()
                failed_count += len(batch)
        except Exception as e:
            logger.error(f"DB Commit error on batch {i // BATCH_SIZE + 1}: {e}")
            db_session.rollback()
            failed_count += len(batch)
    
    if failed_count:
        logger.warning(f"⚠️ {failed_count} products failed to commit.")
    logger.info(f"✅ Processed {processed_count} products successfully.")
        
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
