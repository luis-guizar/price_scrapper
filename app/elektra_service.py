import requests
import logging
import json
import urllib.parse
import concurrent.futures
from datetime import datetime
from app.models import SessionLocal, Product, PriceHistory

# Configurar logging
logger = logging.getLogger(__name__)

class ElektraService:
    def __init__(self, urls):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.elektra.mx/"
        })
        self.urls = urls

    def _fetch_products_from_api(self, url):
        """
        Fetches products from the Elektra/VTEX API.
        URL is expected to be a search query like:
        https://www.elektra.mx/api/catalog_system/pub/products/search?fq=C:123
        """
        found_products = []
        try:
            # Parse URL to preserve existing query params (like fq)
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Ensure we are hitting the API
            if "/api/catalog_system/pub/products/search" not in url:
                # If user provided a category page URL, try to extract ID or conversion?
                # For now, assume user provides API compatible URLs or we need a converter.
                # Let's assume the user puts API links in the txt file for now as per discovery.
                pass

            # Pagination loop
            page_size = 50 # VTEX usually allows up to 50
            _from = 0
            _to = 49
            
            while True:
                # Update pagination params
                query_params['_from'] = [_from]
                query_params['_to'] = [_to]
                
                # Reconstruct URL
                new_query = urllib.parse.urlencode(query_params, doseq=True)
                page_url = urllib.parse.urlunparse(parsed_url._replace(query=new_query))
                
                logger.info(f"Fetching Elektra page range {_from}-{_to}...")
                response = self.session.get(page_url)
                
                # Check for 206 Partial Content or 200 OK
                if response.status_code not in [200, 206]:
                    logger.warning(f"Failed to fetch {page_url}: Status {response.status_code}")
                    break
                
                products_data = response.json()
                
                if not products_data:
                    break
                
                found_products.extend(self._extract_products(products_data))
                
                # Prepare next page
                _from += page_size
                _to += page_size
                
                # Safety break (e.g. max 1000 products per URL for now)
                if _from > 1000:
                   logger.info("Reached safety limit of 1000 products for this URL.")
                   break
                   
        except Exception as e:
            logger.error(f"Error processing Elektra URL {url}: {e}")
            
        return found_products

    def _extract_products(self, products_data):
        extracted = []
        for item in products_data:
            try:
                # Basic info
                pid = item.get("productId")
                if not pid: continue
                
                name = item.get("productName")
                link = item.get("linkText")
                
                # Price logic
                # items[0].sellers[0].commertialOffer.Price
                price = 0
                image = ""
                
                if item.get("items"):
                    first_item = item["items"][0]
                    
                    if first_item.get("images"):
                         image = first_item["images"][0].get("imageUrl", "")
                         
                    if first_item.get("sellers"):
                        seller = first_item["sellers"][0]
                        price = seller.get("commertialOffer", {}).get("Price", 0)
                
                
                full_link = f"https://www.elektra.mx/{link}/p" if link else ""


                if pid and name and price > 0:
                     extracted.append({
                        "name": name,
                        "sku": pid,
                        "url": full_link,
                        "price": float(price),
                        "image": image,
                        "source": "elektra"
                    })
            except Exception as e:
                logger.error(f"Error extracting Elektra product: {e}")
                
        return extracted

    def run(self):
        logger.info(f"Starting Elektra scrape for {len(self.urls)} URLs.")
        all_products = []
        
        # Optimize: Increased workers to 10 since we have multiple search URLs
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self._fetch_products_from_api, url): url for url in self.urls}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    products = future.result()
                    all_products.extend(products)
                    logger.info(f"Extracted {len(products)} products from URL.")
                except Exception as e:
                    logger.error(f"Error processing URL: {e}")
                    
        return all_products

def process_products(products, db_session: SessionLocal):
    alerts = []
    processed_count = 0
    failed_count = 0
    BATCH_SIZE = 50
    
    # Parámetros de Alerta
    MIN_DROP_PCT = 35      # 35% de descuento
    MIN_DROP_AMOUNT = 5000  # O 5000 pesos de bajada directa
    
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i + BATCH_SIZE]
        try:
            for p in batch:
                sku = p['sku']
                url = p['url']
                price = p['price']
                name = p['name']
                
                if not url: continue
                
                # DB Check
                db_product = db_session.query(Product).filter(Product.sku == sku, Product.source == 'elektra').first()
                if not db_product:
                    db_product = db_session.query(Product).filter(Product.url == url).first()
                
                if db_product:
                    old_price = db_product.current_price
                    
                    if price < old_price:
                        drop = old_price - price
                        pct = (drop / old_price) * 100
                        
                        # Alerta si supera el % o el monto fijo
                        if pct >= MIN_DROP_PCT or drop >= MIN_DROP_AMOUNT:
                            alerts.append({
                                "source": "elektra",
                                "title": name,
                                "price": price,
                                "old_price": old_price,
                                "discount_pct": round(pct, 1),
                                "url": url,
                                "sku": sku
                            })
                    
                    if abs(price - old_price) > 0.1:
                        db_product.current_price = price
                        history = PriceHistory(product_id=db_product.id, price=price, timestamp=datetime.now())
                        db_session.add(history)
                        
                    db_product.last_checked = datetime.now()
                    db_product.url = url
                    
                else:
                    new_prod = Product(
                        name=name,
                        sku=sku,
                        url=url,
                        current_price=price,
                        source="elektra",
                        last_checked=datetime.now()
                    )
                    db_session.add(new_prod)
                    db_session.flush() # Get ID
                    history = PriceHistory(product_id=new_prod.id, price=price, timestamp=datetime.now())
                    db_session.add(history)
                
                processed_count += 1
            
            db_session.commit()
            
        except Exception as e:
             logger.error(f"DB Batch Commit error: {e}")
             db_session.rollback()
             failed_count += len(batch)

    if failed_count:
        logger.warning(f"⚠️ {failed_count} products failed to commit.")
    
    return alerts, processed_count

def get_elektra_deals():
    urls = []
    try:
        with open("elektra_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)
    except FileNotFoundError:
        logger.warning("elektra_urls.txt not found")
        
    if not urls:
        return [], 0
        
    service = ElektraService(urls)
    products = service.run()
    
    session = SessionLocal()
    try:
        alerts, count = process_products(products, session)
        return alerts, count
    finally:
        session.close()
