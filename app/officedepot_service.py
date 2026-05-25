import asyncio
import logging
import re
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product
from playwright.async_api import async_playwright

# Configurar logging
logger = logging.getLogger(__name__)

# ==================== CONFIGURACIÓN DE BÚSQUEDA ====================
SEARCH_CONFIG = {
    "urls": [
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Celulares/c/03-1-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/laptops-y-macbook/c/04-039-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Muebles-y-Decoraci%C3%B3n/Sillas/c/06-084-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Impresi%C3%B3n/Impresoras%2C-Multifuncionales-y-Esc%C3%A1neres/c/07-100-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Pantallas/c/03-027-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/ipad-y-tablets/tablets/c/04-041-906-0",
    ],
    "min_price_drop_percent": 50,
    "keywords_include": [],
    "keywords_exclude": [],
    "max_pages": 10,  # Safety limit for pagination
    "concurrency": 2  # Number of concurrent categories to scrape
}

async def fetch_products_from_page(page, url):
    """
    Extracts products from a single page using Playwright.
    Returns a list of product dictionaries.
    """
    products = []
    try:
        # Go to URL with a reasonable timeout
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            # Wait a bit for dataLayer/JS to populate
            await page.wait_for_timeout(3000) 
        except Exception as e:
            logger.error(f"Playwright navigation error for {url}: {e}")
            return []

        # Strategy: Extract from HTML Source (Regex) - Most reliable for Catalog
        try:
            content = await page.content()
            
            # Regex for 'impressions' : [ ... ]
            match = re.search(r"'impressions'\s*:\s*\[(.*?)\]", content, re.DOTALL)
            if match:
                impressions_str = match.group(1)
                item_matches = re.findall(r"\{[^{}]*\}", impressions_str)
                
                if item_matches:
                    for item_str in item_matches:
                        try:
                            id_match = re.search(r"'id'\s*:\s*'([^']*)'", item_str)
                            name_match = re.search(r"'name'\s*:\s*'([^']*)'", item_str)
                            price_match = re.search(r"'price'\s*:\s*'([^']*)'", item_str)
                            
                            if id_match and name_match:
                                pid = id_match.group(1)
                                name = name_match.group(1)
                                price_raw = price_match.group(1) if price_match else "0"
                                
                                if isinstance(price_raw, str):
                                    price_raw = price_raw.replace(',', '')
                                
                                try: price_val = float(price_raw)
                                except: price_val = 0.0
                                
                                product_url = f"https://www.officedepot.com.mx/officedepot/en/p/{pid}"
                                
                                if pid and name and price_val > 0:
                                    products.append({
                                        "@type": "Product",
                                        "name": name,
                                        "sku": pid,
                                        "url": product_url,
                                        "offers": {"price": price_val, "priceCurrency": "MXN"},
                                        "image": ""
                                    })
                        except: pass
            
            # Fallback: Check dataLayer if Regex failed
            if not products:
                data_layer = await page.evaluate("() => window.dataLayer")
                if data_layer and isinstance(data_layer, list):
                    for item in data_layer:
                        if isinstance(item, dict) and 'impressions' in item:
                            impressions = item['impressions']
                            if isinstance(impressions, list):
                                for prod in impressions:
                                    try:
                                        pid = prod.get('id')
                                        name = prod.get('name')
                                        price_raw = prod.get('price', '0')
                                        if isinstance(price_raw, str): price_raw = price_raw.replace(',', '')
                                        try: price_val = float(price_raw)
                                        except: price_val = 0.0
                                        product_url = f"https://www.officedepot.com.mx/officedepot/en/p/{pid}"
                                        if pid and name and price_val > 0:
                                            products.append({
                                                "@type": "Product",
                                                "name": name,
                                                "sku": pid,
                                                "url": product_url,
                                                "offers": {"price": price_val, "priceCurrency": "MXN"},
                                                "image": ""
                                            })
                                    except: pass

        except Exception as e:
            logger.error(f"Extraction error on {url}: {e}")

    except Exception as e:
        logger.error(f"General error on {url}: {e}")
    
    return products

async def scrape_category(context, base_url, semaphore):
    """
    Scrapes a single category, handling pagination until no more products are found
    or max_pages is reached.
    """
    async with semaphore:
        category_products = []
        page_num = 0
        
        while page_num < SEARCH_CONFIG["max_pages"]:
            # Construct URL with pagination
            # Office Depot uses ?q=%3Arelevance&page=X where X starts at 0 or 1.
            # Base URL might not have query params yet.
            # Standard pattern saw in config: .../c/ID?q=%3Arelevance&page=1
            
            if "?" in base_url:
                c_url = f"{base_url}&page={page_num}"
            else:
                c_url = f"{base_url}?q=%3Arelevance&page={page_num}"
            
            logger.info(f"Scraping {c_url}...")
            
            page = await context.new_page()
            try:
                products = await fetch_products_from_page(page, c_url)
                
                if not products:
                    logger.info(f"No products found on page {page_num} for {base_url}. Stopping.")
                    await page.close()
                    break
                
                # Check for duplicates within this scrape session to avoid infinite loops 
                # if the site redirects or shows same content.
                new_products = [p for p in products if p['url'] not in [ep['url'] for ep in category_products]]
                if not new_products:
                     logger.info(f"No NEW products found on page {page_num}. Likely end of list.")
                     await page.close()
                     break

                category_products.extend(new_products)
                logger.info(f"Found {len(new_products)} new products on page {page_num}.")
                
                page_num += 1
                
                # Random delay between pages
                await asyncio.sleep(random.uniform(2, 5))
                
            finally:
                await page.close()

        return category_products

async def runner():
    """
    Main async runner to coordinate scraping.
    """
    all_products = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a single context (like a browser session)
        context = await browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        # Determine concurrency
        semaphore = asyncio.Semaphore(SEARCH_CONFIG["concurrency"])
        
        tasks = []
        for url in SEARCH_CONFIG["urls"]:
            tasks.append(scrape_category(context, url, semaphore))
        
        results = await asyncio.gather(*tasks)
        
        for res in results:
            all_products.extend(res)
            
        await browser.close()
        
    return all_products

def process_products(products):
    """
    Compara los productos encontrados con la base de datos para detectar bajadas de precio.
    Retorna una lista de alertas (deals) y un set de URLs procesadas.
    """
    alerts = []
    processed_urls = set()
    session = SessionLocal()
    
    try:
        seen_urls = set()
        
        for p in products:
            try:
                name = p.get("name")
                url = p.get("url")
                sku = p.get("sku")
                image = p.get("image")
                
                # Obtener precio y ofertas
                offers = p.get("offers", {})
                price = float(offers.get("price", 0))
                
                if not url or price <= 0:
                    continue
                
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                processed_urls.add(url) # Mark as processed

                # Filtrado por keywords
                if SEARCH_CONFIG["keywords_include"]:
                    if not any(k.lower() in name.lower() for k in SEARCH_CONFIG["keywords_include"]):
                        continue
                if SEARCH_CONFIG["keywords_exclude"]:
                    if any(k.lower() in name.lower() for k in SEARCH_CONFIG["keywords_exclude"]):
                        continue

                # Verificar DB por URL primero
                db_product = session.query(Product).filter(Product.url == url).first()
                
                # Si no existe por URL, intentar buscar por SKU para evitar duplicados y errores de unicidad
                if not db_product and sku:
                    db_product = session.query(Product).filter(Product.sku == sku).first()
                    if db_product:
                        # Actualizar URL si ha cambiado para el mismo SKU
                        logger.info(f"Actualizando URL para SKU {sku}: {db_product.url} -> {url}")
                        db_product.url = url

                if db_product:
                    # Producto existe
                    if not db_product.is_active:
                        continue

                    anchor_price = db_product.original_price or db_product.current_price
                    old_price = db_product.current_price

                    # Solo alertar si el precio ACABA de bajar en este scan
                    # Y la bajada acumulada desde original_price supera el threshold
                    if price < old_price and price < anchor_price:
                        drop_amount = anchor_price - price
                        drop_pct = (drop_amount / anchor_price) * 100
                        
                        if drop_pct >= SEARCH_CONFIG["min_price_drop_percent"]:
                            logger.info(f"📉 BAJADA DE PRECIO: {name} (original ${anchor_price} → ${price})")
                            alerts.append({
                                "source": "officedepot",
                                "title": name,
                                "price": price,
                                "old_price": anchor_price,
                                "discount_pct": round(drop_pct, 1),
                                "url": url,
                                "image_url": image,
                                "sku": sku
                            })
                    
                    # Actualizar precio si cambió
                    if abs(price - db_product.current_price) > 0.1:
                        db_product.current_price = price
                    
                    db_product.last_checked = datetime.now()
                    
                else:
                    # Nuevo producto — original_price = primer precio visto
                    # logger.debug(f"Nuevo producto: {name} (${price})")
                    new_product = Product(
                        name=name,
                        url=url,
                        sku=sku,
                        current_price=price,
                        original_price=price,
                        source="officedepot",
                        last_checked=datetime.now()
                    )
                    session.add(new_product)
            
            except Exception as e:
                # logger.error(f"Error procesando item: {e}")
                continue
        
        try:
            session.commit()
        except Exception as e:
            logger.error(f"Error haciendo commit en process_products: {e}")
            session.rollback()
            # Si commit falla, no enviamos alertas porque se volverán a generar como duplicados
            alerts = []

    except Exception as e:
        logger.error(f"Error general en process_products: {e}")
        session.rollback()
    finally:
        session.close()

    return alerts, processed_urls

def get_officedepot_deals():
    try:
        from app.models import init_db
        init_db()
    except:
        pass

    # Run the async scraper
    try:
        # Check if there is an existing loop (e.g. if called from inside another async function, though unlikely for Celery)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # If we are already in an async loop, we should use create_task or similar, 
            # but since this is expected to be called from Celery (sync), this path is rare.
             logger.warning("get_officedepot_deals called from running async loop. This might not work as expected with asyncio.run")
             # Try to schedule it
             future = asyncio.ensure_future(runner())
             products = loop.run_until_complete(future)
        else:
            products = loop.run_until_complete(runner())
            
        logger.info(f"✅ Total officedepot products extracted: {len(products)}")
        
        if products:
            return process_products(products)
        
    except Exception as e:
        logger.error(f"Error running async Office Depot scraper: {e}")
        
    return [], set()

def check_single_officedepot_product(product_id):
    """
    DISABLED: Avoid scrapping prices on product page.
    """
    return None

def update_tracked_products_officedepot(exclude_urls=None):
    """
    DISABLED: Avoid scrapping prices on product page.
    """
    logger.info("🚫 Individual product updates DISABLED for Office Depot (Catalog Only mode).")
    return []
