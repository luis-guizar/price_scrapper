import httpx
import requests
import json
import logging
import re
from datetime import datetime
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from app.models import SessionLocal, Product

# Configurar logging
logger = logging.getLogger(__name__)

# ==================== CONFIGURACIÓN DE BÚSQUEDA ====================
SEARCH_CONFIG = {
    "urls": [

        "https://www.walmart.com.mx/content/celulares/smartphones/264800_264807",
        "https://www.walmart.com.mx/content/tv-y-video/264711",
        "https://www.walmart.com.mx/content/computadoras/laptops/264880_264909",
        "https://www.walmart.com.mx/content/computadoras/tablets/264880_264895",
        "https://www.walmart.com.mx/content/computadoras/computadoras-de-escritorio/264880_264903"
        # Agrega más URLs aquí
    ],
    "min_price_drop_percent": 50, 
    "min_price_drop_amount": 5000, 
}

def fetch_walmart_products(url):
    """
    Obtiene productos de Walmart MX mediante HTML parsing (prioridad) o script parsing (fallback).
    """
    logger.info(f"Escaneando Walmart: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    products = []
    
    try:
        # Usar HTTPX con HTTP/2 para evadir bloqueos básicos
        with httpx.Client(http2=True, timeout=30.0) as client:
            response = client.get(url, headers=headers)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # ---------------------------------------------------------
        # ESTRATEGIA 1: Parsing HTML (Selectores CSS) - Prioridad
        # ---------------------------------------------------------
        # Buscamos contenedores de productos. 
        # Observado en dump: div[role="group"] o data-testid="product-tile-..."
        product_tiles = soup.find_all("div", role="group")
        
        if not product_tiles:
            logger.info("ℹ️ No se encontraron items con role='group', intentando data-testid='product-tile'...")
            product_tiles = soup.select("div[data-testid^='product-tile']")

        if product_tiles:
            logger.info(f"✅ Encontrados {len(product_tiles)} tiles de productos vía HTML.")
            for tile in product_tiles:
                try:
                    # Título: span[data-automation-id="product-title"]
                    title_tag = tile.select_one("span[data-automation-id='product-title']")
                    if not title_tag: continue
                    title = title_tag.get_text(strip=True)

                    # Precio: div[data-automation-id="product-price"]
                    price_tag = tile.select_one("div[data-automation-id='product-price']")
                    price_text = price_tag.get_text(" ", strip=True) if price_tag else "0"
                    
                    # Limpieza de precio "$5,299.00" -> 5299.00
                    # Extraemos números, puntos y comas
                    price_digits = re.findall(r'[0-9,.]+', price_text)
                    if price_digits:
                        # Usamos el primer match
                        price_val = float(price_digits[0].replace(',', ''))
                    else:
                        price_val = 0.0

                    # Link: tag <a>
                    link_tag = tile.find("a")
                    link = link_tag['href'] if link_tag else ""
                    if link and not link.startswith("http"):
                        link = "https://www.walmart.com.mx" + link

                    # Imagen: img[data-testid="productTileImage"]
                    img_tag = tile.select_one("img[data-testid='productTileImage']")
                    image_url = img_tag['src'] if img_tag else ""

                    if title and price_val > 0:
                        products.append({
                            "name": title,
                            "url": link,
                            "sku": link.split('/')[-1].split('?')[0] if link else "",
                            "image": image_url,
                            "offers": {
                                "price": price_val,
                                "priceCurrency": "MXN"
                            }
                        })
                except Exception as e:
                    continue

        # ---------------------------------------------------------
        # ESTRATEGIA 2: Fallback a JSON Parsing (Scripts)
        # ---------------------------------------------------------
        if not products:
             logger.info("⚠️ Parsing HTML retornó 0 productos. Intentando fallback scripts...")
             
             data = None
             # Intento 1: ID explícito
             next_data_script = soup.find("script", id="__NEXT_DATA__")
             if next_data_script:
                 try:
                     data = json.loads(next_data_script.string)
                 except: pass
            
             # Intento 2: Buscar en todos los scripts
             if not data:
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.get("src"): continue
                    content = script.string
                    if content and 'initialState' in content and 'pageProps' in content:
                        try:
                            possible_data = json.loads(content)
                            if 'props' in possible_data and 'pageProps' in possible_data:
                                data = possible_data
                                break
                        except: continue

             if data:
                 try:
                     # Path común: props -> pageProps -> initialData -> searchResult -> itemStacks -> [0] -> items
                     initial_data = data.get('props', {}).get('pageProps', {}).get('initialData', {})
                     search_result = initial_data.get('searchResult', {})
                     item_stacks = search_result.get('itemStacks', [])
                     if item_stacks:
                         items = item_stacks[0].get('items', [])
                         for item in items:
                             p_title = item.get('name', '')
                             p_price = float(item.get('price', 0))
                             canonical = item.get('canonicalUrl', '')
                             p_url = f"https://www.walmart.com.mx{canonical}" if canonical else ""
                             p_image = item.get('image', '')
                             p_id = item.get('id', '')

                             if p_title and p_price > 0:
                                 products.append({
                                    "name": p_title,
                                    "url": p_url,
                                    "sku": p_id,
                                    "image": p_image,
                                    "offers": {
                                        "price": p_price,
                                        "priceCurrency": "MXN"
                                    }
                                 })
                 except Exception as e:
                     logger.error(f"Error en JSON fallback: {e}")

        # ---------------------------------------------------------
        # Verificamos Bloqueo REAL (Solo si no hay productos)
        # ---------------------------------------------------------
        if not products:
            text_lower = response.text.lower()
            # Chequeo estricto: debe haber keywords de bloqueo Y 0 productos
            if "robot check" in text_lower or "captcha" in text_lower or "perimeterx" in text_lower:
                logger.warning(f"⚠️ BLOQUEO DETECTADO CONFIRMADO EN: {url}")
            else:
                logger.warning(f"❌ Parsing falló en {url}. 0 productos encontrados. Guardando dump.")
            
            try:
                with open("failed_dump.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
            except: pass

    except Exception as e:
        logger.error(f"Error general en fetch_walmart_products: {e}")

    logger.info(f"✅ Total productos válidos extraídos: {len(products)}")
    return products

def process_products(products):
    """
    Compara los productos encontrados con la DB para detectar bajadas.
    Reutiliza lógica similar a Office Depot.
    """
    alerts = []
    session = SessionLocal()
    
    try:
        for p in products:
            try:
                name = p.get("name")
                url = p.get("url")
                sku = p.get("sku")
                image = p.get("image")
                
                # Obtener precio
                offers = p.get("offers", {})
                price = float(offers.get("price", 0))
                
                if not url or price <= 0:
                    continue

                # Verificar DB
                db_product = session.query(Product).filter(Product.url == url).first()
                
                if db_product:
                    old_price = db_product.current_price
                    
                    # Detectar bajada
                    if price < old_price:
                        drop_amount = old_price - price
                        drop_pct = (drop_amount / old_price) * 100
                        
                        if drop_pct >= SEARCH_CONFIG["min_price_drop_percent"] or drop_amount >= SEARCH_CONFIG["min_price_drop_amount"]:
                            logger.info(f"📉 BAJADA DE PRECIO: {name} (${old_price} -> ${price})")
                            alerts.append({
                                "source": "walmart",
                                "title": name,
                                "price": price,
                                "old_price": old_price,
                                "discount_pct": round(drop_pct, 1),
                                "url": url,
                                "image_url": image,
                                "sku": sku
                            })
                    
                    # Actualizar precio
                    if abs(price - db_product.current_price) > 0.1:
                        db_product.current_price = price
                    
                    db_product.last_checked = datetime.utcnow()
                    
                else:
                    # Nuevo producto
                    new_product = Product(
                        name=name,
                        url=url,
                        current_price=price,
                        last_checked=datetime.utcnow()
                    )
                    session.add(new_product)
            
            except Exception as e:
                logger.error(f"Error procesando item {p.get('name')}: {e}")
                continue
        
        session.commit()
    except Exception as e:
        logger.error(f"Error general en process_products: {e}")
        session.rollback()
    finally:
        session.close()

    return alerts

def get_walmart_deals():
    try:
        from app.models import init_db
        init_db()
    except:
        pass

    all_alerts = []
    for url in SEARCH_CONFIG["urls"]:
        products = fetch_walmart_products(url)
        if products:
            alerts = process_products(products)
            all_alerts.extend(alerts)
            
    return all_alerts
