import requests
import json
import logging
import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product, PriceHistory
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time

# Configurar logging
logger = logging.getLogger(__name__)

# ==================== CONFIGURACIÓN DE BÚSQUEDA ====================
SEARCH_CONFIG = {
    "urls": [
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0?q=%3Arelevance&page=1",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Celulares/c/03-1-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Celulares/c/03-1-0-0?q=%3Arelevance&page=1",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Celulares/c/03-1-0-0?q=%3Arelevance&page=2",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/laptops-y-macbook/c/04-039-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/laptops-y-macbook/c/04-039-0-0?q=%3Arelevance&page=1",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/laptops-y-macbook/c/04-039-0-0?q=%3Arelevance&page=2",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/laptops-y-macbook/c/04-039-0-0?q=%3Arelevance&page=3",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Muebles-y-Decoraci%C3%B3n/Sillas/c/06-084-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Muebles-y-Decoraci%C3%B3n/Sillas/c/06-084-0-0?q=%3Arelevance&page=1",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Muebles-y-Decoraci%C3%B3n/Sillas/c/06-084-0-0?q=%3Arelevance&page=2",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Muebles-y-Decoraci%C3%B3n/Sillas/c/06-084-0-0?q=%3Arelevance&page=3",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Impresi%C3%B3n/Impresoras%2C-Multifuncionales-y-Esc%C3%A1neres/c/07-100-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Impresi%C3%B3n/Impresoras%2C-Multifuncionales-y-Esc%C3%A1neres/c/07-100-0-0?q=%3Arelevance&page=1",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Impresi%C3%B3n/Impresoras%2C-Multifuncionales-y-Esc%C3%A1neres/c/07-100-0-0?q=%3Arelevance&page=2",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Pantallas/c/03-027-0-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Pantallas/c/03-027-0-0?q=%3Arelevance&page=1",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Pantallas/c/03-027-0-0?q=%3Arelevance&page=2",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/ipad-y-tablets/tablets/c/04-041-906-0",
        "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/ipad-y-tablets/tablets/c/04-041-906-0?q=%3Arelevance&page=1"
    ],
    "min_price_drop_percent": 50,
    "min_price_drop_amount": 5000,
    "keywords_include": [],
    "keywords_exclude": [],
}

def fetch_officedepot_products(url):
    """
    Obtiene productos usando Playwright para renderizar JS y acceder a dataLayer.
    Estrategia unica: DataLayer 'impressions' en catalogo.
    """
    logger.info(f"Escaneando Office Depot (Playwright): {url}")
    products = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Go to URL
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                # Wait for dataLayer population
                page.wait_for_timeout(5000)
            except Exception as e:
                logger.error(f"Playwright navigation error (ignorable): {e}")

            # Strategy: Extract from HTML Source (Regex) - Most reliable for Catalog
            try:
                content = page.content()
                import re
                
                # Regex for 'impressions' : [ ... ]
                match = re.search(r"'impressions'\s*:\s*\[(.*?)\]", content, re.DOTALL)
                if match:
                    impressions_str = match.group(1)
                    item_matches = re.findall(r"\{[^{}]*\}", impressions_str)
                    
                    if item_matches:
                        # logger.info(f"🔍 Found {len(item_matches)} items via Regex.")
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
                
                # Check results
                if not products:
                     # Check dataLayer as fallback if Regex failed (unlikely but possible)
                     data_layer = page.evaluate("() => window.dataLayer")
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
                logger.error(f"Extraction error: {e}")
            finally:
                browser.close()

    except Exception as e:
        logger.error(f"Error initializing Playwright for {url}: {e}")
    
    logger.info(f"✅ Total productos extraídos: {len(products)}")
    return products

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
                    # Producto existe, comparar precio
                    old_price = db_product.current_price
                    
                    # Detectar bajada
                    if price < old_price:
                        drop_amount = old_price - price
                        drop_pct = (drop_amount / old_price) * 100
                        
                        if drop_pct >= SEARCH_CONFIG["min_price_drop_percent"] or drop_amount >= SEARCH_CONFIG["min_price_drop_amount"]:
                            logger.info(f"📉 BAJADA DE PRECIO: {name} (${old_price} -> ${price})")
                            alerts.append({
                                "source": "officedepot",
                                "title": name,
                                "price": price,
                                "old_price": old_price,
                                "discount_pct": round(drop_pct, 1),
                                "url": url,
                                "image_url": image,
                                "sku": sku
                            })
                    
                    # Actualizar precio si cambió
                    if abs(price - db_product.current_price) > 0.1:
                        db_product.current_price = price
                        # Add to history
                        history = PriceHistory(product=db_product, price=price, timestamp=datetime.utcnow())
                        session.add(history)
                    
                    db_product.last_checked = datetime.utcnow()
                    
                else:
                    # Nuevo producto
                    # logger.debug(f"Nuevo producto: {name} (${price})")
                    new_product = Product(
                        name=name,
                        url=url,
                        sku=sku,
                        current_price=price,
                        source="officedepot",
                        last_checked=datetime.utcnow()
                    )
                    session.add(new_product)
                    
                    # Add initial history
                    history = PriceHistory(product=new_product, price=price, timestamp=datetime.utcnow())
                    session.add(history)
            
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

    all_alerts = []
    all_processed_urls = set()
    
    for url in SEARCH_CONFIG["urls"]:
        products = fetch_officedepot_products(url)
        if products:
            alerts, processed = process_products(products)
            all_alerts.extend(alerts)
            all_processed_urls.update(processed)
            
    return all_alerts, all_processed_urls

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
