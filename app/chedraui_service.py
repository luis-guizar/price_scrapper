import requests
import logging
import json
import urllib.parse
import concurrent.futures
import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product
import re
from bs4 import BeautifulSoup

# Configurar logging
logger = logging.getLogger(__name__)

class ChedrauiService:
    def __init__(self, urls):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.chedraui.com.mx/"
        })
        self.products = []
        
        # Deduplicate URLs based on the 'query' variable to avoid processing the same category multiple times
        self.urls = []
        seen_queries = set()
        for url in urls:
            try:
                parsed = urllib.parse.urlparse(url)
                qs = urllib.parse.parse_qs(parsed.query)
                if 'variables' in qs:
                    vars_json = json.loads(qs['variables'][0])
                    query = vars_json.get('query')
                    if query and query in seen_queries:
                        continue
                    if query:
                        seen_queries.add(query)
                self.urls.append(url)
            except Exception:
                self.urls.append(url)


    def _fetch_page(self, base_url, variables, page_index, page_size=20):
        try:
            import base64
            
            # Reconstruct URL components first
            parsed_url = urllib.parse.urlparse(base_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Case 1: Variables are in 'extensions' (Base64 encoded)
            if 'extensions' in query_params:
                try:
                    ext_str = query_params['extensions'][0]
                    ext_json = json.loads(ext_str)
                    
                    if 'persistedQuery' in ext_json and 'variables' in ext_json:
                        # Decode variables from base64
                        decoded_vars_str = base64.b64decode(ext_json['variables']).decode('utf-8')
                        decoded_vars = json.loads(decoded_vars_str)
                        
                        # Update pagination
                        decoded_vars["from"] = page_index * page_size
                        decoded_vars["to"] = (page_index + 1) * page_size - 1
                        decoded_vars["page"] = page_index + 1
                        
                        # Re-encode to base64
                        encoded_vars_str = base64.b64encode(json.dumps(decoded_vars).encode('utf-8')).decode('utf-8')
                        ext_json['variables'] = encoded_vars_str
                        
                        # Update query params
                        query_params['extensions'] = [json.dumps(ext_json)]
                        
                except Exception as e:
                    logger.error(f"Error handling extensions pagination: {e}")
                    # Fallback to standard variables handling if this complex logic fails
                    pass

            # Case 2: Variables are top-level or logic failing back to top-level
            # (We perform this update regardless, or careful not to overwrite if extension logic succeeded but I will err on side of updating "variables" param too if it exists)
            
            # Update local variables dict (argument) just in case it's used elsewhere or if 'variables' param is dominant
            variables["from"] = page_index * page_size
            variables["to"] = (page_index + 1) * page_size - 1
            variables["page"] = page_index + 1 
            
            if 'variables' in query_params:
                 query_params['variables'] = [json.dumps(variables)]

            
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            page_url = urllib.parse.urlunparse(parsed_url._replace(query=new_query))
            
            logger.info(f"Fetching page {page_index}...")
            response = self.session.get(page_url)
            response.raise_for_status()
            
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"Error fetching page {page_index}: {e}")
            return None

    def _process_url(self, url):
        """Process a single search URL including pagination."""
        found_products = []
        try:
            # Parse initial URL to get variables
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if 'variables' not in query_params:
                logger.error(f"No variables found in URL: {url}")
                return []
                
            variables_str = query_params['variables'][0]
            variables = json.loads(variables_str)
            
            # Initial fetch to get total count
            data = self._fetch_page(url, variables, 0)
            if not data:
                return []
                
            product_search = data.get("data", {}).get("productSearch", {})
            products_data = product_search.get("products", [])
            # Check for recordsFiltered, default to None if missing
            records_filtered = product_search.get("recordsFiltered")
            
            if not products_data:
                logger.warning(f"No products found for {url}")
                return []

            if records_filtered is not None:
                logger.info(f"Found {records_filtered} total items.")
                found_products.extend(self._extract_products(products_data))
                
                # Calculate total pages
                page_size = 20
                import math
                total_pages = math.ceil(records_filtered / page_size)
                
                if total_pages > 1:
                    for page in range(1, total_pages):
                         page_data = self._fetch_page(url, variables, page)
                         if page_data:
                             p_data = page_data.get("data", {}).get("productSearch", {}).get("products", [])
                             if p_data:
                                found_products.extend(self._extract_products(p_data))
                             else:
                                break
            else:
                 # If no total count, loop until empty
                 logger.info("No recordsFiltered found, using infinite scroll logic.")
                 found_products.extend(self._extract_products(products_data))
                 page = 1
                 while True:
                     page_data = self._fetch_page(url, variables, page)
                     if not page_data:
                         break
                         
                     p_data = page_data.get("data", {}).get("productSearch", {}).get("products", [])
                     if not p_data:
                         break
                         
                     found_products.extend(self._extract_products(p_data))
                     page += 1
                     
                     # Safety breaker
                     if page > 50:
                         logger.warning(f"Reached 50 pages for {url}, stopping safety.")
                         break

            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            
        return found_products

    def _extract_products(self, products_data):
        extracted = []
        for item in products_data:
            try:
                # Basic extraction
                pid = item.get("productId")
                name = item.get("productName")
                link = item.get("link")
                
                # Price extraction
                price_range = item.get("priceRange")
                selling_price = 0
                if price_range:
                    selling_price = price_range.get("sellingPrice", {}).get("highPrice", 0)
                
                # Image extraction
                image = ""
                if item.get("items") and len(item['items']) > 0:
                    images = item['items'][0].get("images", [])
                    if images:
                        image = images[0].get("imageUrl", "")
                
                # Convert price (it seems to be in cents or needs check, usually VTEX is raw but check example)
                # Example: "highPrice": 9995 -> 99.95 or 9995? 
                # Checking response: 18995 for "Laptop HP...". Usually prices in MXN are like 18995.00
                # Wait, "highPrice": 9995 for a laptop? That's cheap if it's 9,995. 
                # Let's assume it's the float value directly or needs /100?
                # "Price":9995 in commertialOffer.
                # If it is 9995 cents, it would be 99 pesos. A laptop is not 99 pesos.
                # So it is 9995 pesos.
                
                full_link = f"https://www.chedraui.com.mx{link}" if link else ""
                
                if pid and name and selling_price > 0:
                     extracted.append({
                        "name": name,
                        "sku": pid,
                        "url": full_link,
                        "price": float(selling_price),
                        "image": image,
                        "source": "chedraui"
                    })
                else:
                    logger.debug(f"Skipping product {pid}: name={bool(name)}, price={selling_price}")
            except Exception as e:
                logger.error(f"Error extracting product: {e}")
        return extracted

    def run(self):
        logger.info(f"Starting Chedraui scrape for {len(self.urls)} URLs.")
        all_products = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(self._process_url, url): url for url in self.urls}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    products = future.result()
                    all_products.extend(products)
                    logger.info(f"Extracted {len(products)} products from URL.")
                except Exception as e:
                    logger.error(f"Error requires url processing: {e}")
                    
        return all_products

def process_products(products, db_session: Session):
    """
    Save products to DB and check for alerts.
    """
    alerts = []
    processed_count = 0
    failed_count = 0
    BATCH_SIZE = 50
    
    # Configuration for alerts
    MIN_DROP_PCT = 50
    
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i + BATCH_SIZE]
        batch_ok = True
        
        for p in batch:
            try:
                sku = p['sku']
                url = p['url']
                price = p['price']
                name = p['name']
                
                if not url:
                    continue
                
                # Find existing product
                db_product = db_session.query(Product).filter(Product.sku == sku, Product.source == 'chedraui').first()
                # Also try by URL if SKU not found (though SKU is safer)
                if not db_product:
                     db_product = db_session.query(Product).filter(Product.url == url).first()
                
                if db_product:
                    if not db_product.is_active:
                        continue

                    anchor_price = db_product.original_price or db_product.current_price
                    old_price = db_product.current_price
                    
                    # Only alert if price JUST dropped AND cumulative drop exceeds threshold
                    if price < old_price and price < anchor_price:
                        drop = anchor_price - price
                        pct = (drop / anchor_price) * 100
                        
                        if pct >= MIN_DROP_PCT:
                            # Validate price drop before alerting
                            logger.info(f"📍 Potential deal detected: {name} (original ${anchor_price} → ${price}). Validating...")
                            if validate_price_drop(url, price, anchor_price):
                                alerts.append({
                                    "source": "chedraui",
                                    "title": name,
                                    "price": price,
                                    "old_price": anchor_price,
                                    "discount_pct": round(pct, 1),
                                    "url": url,
                                    "sku": sku
                                })
                            else:
                                logger.info(f"🚫 Precio drop falso positivo descartado: {name}")
                    
                    if abs(price - old_price) > 0.1:
                        db_product.current_price = price
                    
                    # Backfill original_price if NULL
                    if not db_product.original_price:
                        db_product.original_price = old_price
                        
                    db_product.last_checked = datetime.now() # type: ignore
                    db_product.url = url # Update URL just in case
                    
                else:
                    new_prod = Product(
                        name=name,
                        sku=sku,
                        url=url,
                        current_price=price,
                        original_price=price,
                        source="chedraui",
                        last_checked=datetime.now()
                    )
                    db_session.add(new_prod)
                    db_session.flush()
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing product {p.get('sku')}: {e}")
                batch_ok = False
                break
        
        try:
            if batch_ok:
                db_session.commit()
            else:
                db_session.rollback()
                failed_count += len(batch)
        except Exception as e:
             logger.error(f"DB Commit error: {e}")
             db_session.rollback()
             failed_count += len(batch)

    if failed_count:
        logger.warning(f"⚠️ {failed_count} products failed to commit.")
    
    return alerts, processed_count

def fetch_single_product_price(product_url):
    """
    Fetch the price of a single product directly from its product page.
    This is used to validate if a price drop is real (not a temporary API glitch).
    
    Returns: float price if found, None if error
    """
    if not product_url:
        return None
        
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        response = session.get(product_url, timeout=10)
        response.raise_for_status()
        
        # Strategy 1: Look for JSON-LD structured data (most reliable)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            json_ld = soup.find('script', {'type': 'application/ld+json'})
            if json_ld:
                data = json.loads(json_ld.string) # type: ignore
                if isinstance(data, dict) and 'offers' in data:
                    offers = data['offers']
                    
                    # Handle AggregateOffer (highPrice/lowPrice)
                    if isinstance(offers, dict):
                        # Try highPrice first (lista price)
                        if 'highPrice' in offers:
                            price = float(offers['highPrice'])
                            if price > 0:
                                logger.info(f"✅ Extracted price from JSON-LD highPrice: ${price}")
                                return price
                        # Try price as fallback
                        if 'price' in offers:
                            price = float(offers['price'])
                            if price > 0:
                                logger.info(f"✅ Extracted price from JSON-LD price: ${price}")
                                return price
                    
                    # Handle array of offers
                    elif isinstance(offers, list) and len(offers) > 0:
                        offer = offers[0]
                        if isinstance(offer, dict):
                            for key in ['highPrice', 'price']:
                                if key in offer:
                                    price = float(offer[key])
                                    if price > 0:
                                        logger.info(f"✅ Extracted price from JSON-LD {key}: ${price}")
                                        return price
        except Exception as e:
            logger.debug(f"Could not extract price from JSON-LD: {e}")
        
        # Strategy 2: Look for meta og:price (Open Graph)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_price = soup.find('meta', {'property': 'product:price:amount'})
            if meta_price and meta_price.get('content'):
                price = float(meta_price['content']) # type: ignore
                if price > 0:
                    logger.info(f"✅ Extracted price from meta tag: ${price}")
                    return price
        except Exception as e:
            logger.debug(f"Could not extract from meta tags: {e}")
        
        logger.warning(f"Could not extract price from {product_url}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching single product price from {product_url}: {e}")
        return None


def validate_price_drop(url, detected_new_price, original_db_price):
    """
    Validate if a detected price drop is real by re-fetching after a delay.
    
    Returns: True if drop is confirmed, False if it was a temporary glitch
    """
    try:
        # Esperar un poco para asegurar que no es un glitch de cache
        time.sleep(1)
        
        # Re-fetch el precio del producto
        refetched_price = fetch_single_product_price(url)
        
        if refetched_price is None:
            logger.warning(f"Could not re-fetch price for {url}, assuming glitch")
            return False
        
        logger.info(f"Price validation for {url}: original=${original_db_price} → detected=${detected_new_price} → re-fetched=${refetched_price}")
        
        # Si el precio se recuperó, fue un falso positivo
        if abs(refetched_price - original_db_price) < 100:  # Tolerancia de $100
            logger.info(f"⚠️ FALSE POSITIVE: Precio se recuperó de ${detected_new_price} a ${refetched_price}")
            return False
        
        # Si el precio sigue bajo, es una bajada real
        if refetched_price < original_db_price:
            logger.info(f"✅ CONFIRMED: Precio bajó a ${refetched_price} (de ${original_db_price})")
            return True
        
        logger.info(f"Price validation: bajada temporal detectada pero precio se recuperó")
        return False
        
    except Exception as e:
        logger.error(f"Error validating price drop: {e}")
        return False


def get_chedraui_deals():
    urls = []
    try:
        with open("chedraui_example_api_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)
    except FileNotFoundError:
        logger.warning("chedraui_example_api_urls.txt not found")
        
    if not urls:
        return [], 0
        
    service = ChedrauiService(urls)
    products = service.run()
    
    session = SessionLocal()
    try:
        alerts, count = process_products(products, session)
        return alerts, count
    finally:
        session.close()
