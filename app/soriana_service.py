import requests
import logging
import urllib.parse
import concurrent.futures
import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product
from bs4 import BeautifulSoup

# Configurar logging
logger = logging.getLogger(__name__)

class SorianaService:
    def __init__(self, urls):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "Referer": "https://www.soriana.com/",
            "Connection": "keep-alive"
        })
        self.urls = urls

    def _fetch_page(self, base_url, start, sz=100, retries=2):
        """Fetch a specific page with retry logic."""
        for attempt in range(retries + 1):
            try:
                parsed_url = urllib.parse.urlparse(base_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                # Update pagination parameters
                query_params['start'] = [str(start)]
                query_params['sz'] = [str(sz)]
                page_number = (start // sz) + 1
                query_params['pageNumber'] = [str(page_number)]
                
                new_query = urllib.parse.urlencode(query_params, doseq=True)
                page_url = urllib.parse.urlunparse(parsed_url._replace(query=new_query))
                
                logger.info("Fetching Soriana page at start=%s (sz=%s) [Attempt %s/%s]...", start, sz, attempt+1, retries+1)
                response = self.session.get(page_url, timeout=15)
                
                if response.status_code == 500 and sz > 24:
                    logger.warning(f"500 Error with sz={sz}, falling back to sz=24...")
                    return self._fetch_page(base_url, start, sz=24, retries=0)
                
                response.raise_for_status()
                return response.text
                
            except Exception as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Retry {attempt+1} for Soriana start={start} after {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch Soriana page at start {start} after {retries+1} attempts: {e}")
        return None

    def _extract_products(self, html_content):
        """Parse products from the HTML fragment."""
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted = []
        
        product_divs = soup.find_all('div', class_='product')
        
        for div in product_divs:
            try:
                pid = div.get('data-pid')
                
                # Name & URL
                name_tag = div.find('a', class_='product-tile--link')
                if not name_tag:
                    continue
                    
                name = " ".join(name_tag.get_text(strip=True).split())
                url = name_tag.get('href')
                if url and not url.startswith('http'):
                    url = f"https://www.soriana.com{url}"
                
                # Price extraction
                price_input = div.find('input', {'name': 'clevertap-price'})
                list_price_input = div.find('input', {'name': 'clevertap-list-price'})
                
                original_price = float(list_price_input.get('value')) if list_price_input else 0.0
                
                if price_input:
                    current_price = float(price_input.get('value'))
                else:
                    # If no sale price, current price is the list price
                    current_price = original_price
                    original_price = 0.0
                
                # Image
                img_tag = div.find('img', class_='tile-image')
                image_url = ""
                if img_tag:
                    image_url = img_tag.get('data-src') or img_tag.get('src')
                
                if pid and name and current_price > 0:
                    extracted.append({
                        "name": name,
                        "sku": pid,
                        "url": url,
                        "price": current_price,
                        "original_price": original_price,
                        "image": image_url,
                        "source": "soriana"
                    })
            except Exception as e:
                logger.error(f"Error extracting Soriana product: {e}")
                
        return extracted

    def _process_url(self, url):
        """Process a single category URL with pagination."""
        all_found = []
        start = 0
        sz = 100
        max_pages = 10 # Safety limit
        
        for page in range(max_pages):
            html = self._fetch_page(url, start, sz)
            if not html:
                break
                
            products = self._extract_products(html)
            if not products:
                break
                
            all_found.extend(products)
            
            # If we got fewer products than requested, we reached the end
            if len(products) < sz:
                break
                
            start += sz
            time.sleep(0.5) # Reduced delay since we have more concurrency
            
        return all_found

    def run(self):
        logger.info("Starting Soriana scrape for %s root URLs.", len(self.urls))
        all_products = []
        
        # Increased workers for faster processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self._process_url, url): url for url in self.urls}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    products = future.result()
                    all_products.extend(products)
                    logger.info(f"Extracted {len(products)} products from category.")
                except Exception as e:
                    logger.error(f"Error processing Soriana URL: {e}")
                    
        return all_products

def process_products(products, db_session: Session):
    """
    Save products to DB and check for alerts.
    """
    alerts = []
    processed_count = 0
    
    # Configuration for alerts
    MIN_DROP_PCT = 50
    
    for p in products:
        try:
            sku = p['sku']
            url = p['url']
            price = p['price']
            name = p['name']
            
            # Find existing product
            db_product = db_session.query(Product).filter(Product.sku == sku, Product.source == 'soriana').first()
            
            if db_product:
                anchor_price = db_product.original_price or db_product.current_price
                old_price = db_product.current_price
                
                # Only alert if price JUST dropped AND cumulative drop exceeds threshold
                if price < old_price and price < anchor_price:
                    drop = anchor_price - price
                    pct = (drop / anchor_price) * 100
                    
                    if pct >= MIN_DROP_PCT:
                        alerts.append({
                            "source": "soriana",
                            "title": name,
                            "price": price,
                            "old_price": anchor_price,
                            "discount_pct": round(pct, 1),
                            "url": url,
                            "sku": sku
                        })
                
                # Update price if changed
                if abs(price - old_price) > 0.1:
                    db_product.current_price = price
                
                # Backfill original_price if NULL
                if not db_product.original_price:
                    db_product.original_price = old_price
                    
                db_product.last_checked = datetime.now()
                db_product.url = url 
                
            else:
                # New product — use scraped original_price if available, otherwise current price
                new_prod = Product(
                    name=name,
                    sku=sku,
                    url=url,
                    current_price=price,
                    original_price=p.get('original_price') or price,
                    source="soriana",
                    last_checked=datetime.now()
                )
                db_session.add(new_prod)
                db_session.flush() # Get ID
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing product {p.get('sku')}: {e}")
            db_session.rollback()
            continue
            
    try:
        db_session.commit()
    except Exception as e:
        logger.error(f"DB Commit error: {e}")
        db_session.rollback()

    return alerts, processed_count

def get_soriana_deals():
    urls = []
    try:
        with open("soriana_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)
    except FileNotFoundError:
        logger.warning("soriana_urls.txt not found")
        
    if not urls:
        return [], 0
        
    service = SorianaService(urls)
    products = service.run()
    
    session = SessionLocal()
    try:
        alerts, count = process_products(products, session)
        return alerts, count
    finally:
        session.close()
