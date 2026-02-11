import requests
import json
import logging
import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product
from bs4 import BeautifulSoup

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
    Obtiene productos usando BeautifulSoup para encontrar el script dataLayer,
    que contiene un listado más completo de productos y precios 'sale_price'.
    Fallback: JSON-LD standard.
    """
    logger.info(f"Escaneando Office Depot: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    products = []
    
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    # --- ESTRATEGIA 1: DataLayer (Más completa y con sale_price) ---
    scripts = soup.find_all('script')
    found_datalayer = None
    
    # Buscar script que contenga dataLayer.push y impressions
    for script in scripts:
        # .string a veces es None si hay comentarios complejos o estructura, usar text o get_text
        txt = script.get_text() or ''
        if 'dataLayer.push' in txt and 'impressions' in txt:
            found_datalayer = txt
            break
            
    if found_datalayer:
        try:
            # Extraer el bloque 'impressions': [ ... ]
            match = re.search(r"'impressions'\s*:\s*\[(.*?)\]", found_datalayer, re.DOTALL)
            if match:
                impressions_str = match.group(1)
                
                # Iterar sobre objetos { ... }
                # Regex para capturar bloques entre llaves
                # Nota: esto asume que no hay llaves anidadas complejas dentro de los valores
                item_matches = re.findall(r"\{[^{}]*\}", impressions_str)
                
                logger.info(f"🔍 Encontrados {len(item_matches)} items en dataLayer")
                
                for item_str in item_matches:
                    # Extraer campos con regex
                    id_match = re.search(r"'id'\s*:\s*'([^']*)'", item_str)
                    name_match = re.search(r"'name'\s*:\s*'([^']*)'", item_str)
                    price_match = re.search(r"'price'\s*:\s*'([^']*)'", item_str)
                    sale_price_match = re.search(r"'sale_price'\s*:\s*'([^']*)'", item_str)
                    
                    if id_match and name_match:
                        pid = id_match.group(1)
                        name = name_match.group(1)
                        price_raw = price_match.group(1) if price_match else "0"
                        sale_price_raw = sale_price_match.group(1) if sale_price_match else None
                        
                        # Determinar el precio real (el menor)
                        try:
                            p_val = float(price_raw)
                        except:
                            p_val = 0.0
                            
                        try:
                            if sale_price_raw:
                                sp_val = float(sale_price_raw)
                                # Usar sale_price si es válido y menor que precio normal
                                if sp_val > 0 and sp_val < p_val:
                                    p_val = sp_val
                        except:
                            pass
                            
                        if p_val > 0:
                            product_obj = {
                                "@type": "Product",
                                "name": name,
                                "sku": pid,
                                "url": f"https://www.officedepot.com.mx/officedepot/en/p/{pid}", # Construir URL
                                "offers": {
                                    "price": p_val,
                                    "priceCurrency": "MXN"
                                },
                                "image": "" # No viene en dataLayer, dejamos vacio
                            }
                            products.append(product_obj)
        except Exception as e:
            logger.error(f"Error parseando dataLayer: {e}")

    # --- ESTRATEGIA 2: JSON-LD (Fallback o suplemento) ---
    # Si dataLayer falló o queremos asegurar, buscamos JSON-LD
    # Pero priorizamos dataLayer porque tiene sale_price
    
    if not products:
        logger.info("⚠️ DataLayer no encontrado o vacío, intentando JSON-LD...")
        json_ld_matches = re.findall(r'<script.*?type="application/ld\+json".*?>(.*?)</script>', response.text, re.DOTALL)
        for script_content in json_ld_matches:
            try:
                data = json.loads(script_content)
                if isinstance(data, list): items_list = data
                else: items_list = [data]
                
                for item in items_list:
                    if item.get("mainEntity", {}).get("@type") == "ItemList":
                            for element in item["mainEntity"].get("itemListElement", []):
                                if element.get("@type") == "Product":
                                    products.append(element)
                    elif item.get("@type") == "ItemList":
                            for element in item.get("itemListElement", []):
                                if element.get("@type") == "Product":
                                    products.append(element)
            except:
                continue
    
    # Eliminar duplicados por SKU/URL si mezclamos estrategias (aunque aquí es if/else implícito)
    # Dejamos tal cual por ahora
    
    logger.info(f"✅ Total productos extraídos: {len(products)}")
    return products

def process_products(products):
    """
    Compara los productos encontrados con la base de datos para detectar bajadas de precio.
    Retorna una lista de alertas (deals).
    """
    alerts = []
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

    return alerts

def get_officedepot_deals():
    try:
        from app.models import init_db
        init_db()
    except:
        pass

    all_alerts = []
    for url in SEARCH_CONFIG["urls"]:
        products = fetch_officedepot_products(url)
        if products:
            alerts = process_products(products)
            all_alerts.extend(alerts)
            
    return all_alerts

def update_tracked_products_officedepot():
    """
    Actualiza productos individuales de OfficeDepot (source='officedepot')
    """
    logger.info("🔄 Actualizando productos rastreados de Office Depot...")
    session = SessionLocal()
    alerts = []
    
    try:
        products = session.query(Product).filter(Product.source == 'officedepot').all()
        logger.info(f"   -> {len(products)} productos a revisar.")
        
        for product in products:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                response = requests.get(product.url, headers=headers, timeout=20)
                if response.status_code != 200:
                     continue
                     
                soup = BeautifulSoup(response.text, 'lxml')
                price = 0.0
                
                # Intentar buscar precio en JSON-LD (Product)
                json_ld_scripts = soup.find_all('script', type="application/ld+json")
                for script in json_ld_scripts:
                     try:
                         data = json.loads(script.string)
                         # Puede ser una lista o dict
                         if isinstance(data, list): 
                             items = data
                         else:
                             items = [data]
                             
                         for item in items:
                             if item.get('@type') == 'Product':
                                 offers = item.get('offers', {})
                                 price = float(offers.get('price', 0))
                                 if price > 0: break
                     except: pass
                     if price > 0: break

                # Fallback: Meta tags
                if price == 0:
                     # <meta property="product:price:amount" content="1234.56" />
                     meta = soup.find('meta', property="product:price:amount")
                     if meta:
                         try: price = float(meta['content'])
                         except: pass

                if price > 0:
                    old_price = product.current_price
                    
                    if abs(price - old_price) > 0.1:
                        product.current_price = price
                        # History
                        from app.models import PriceHistory
                        history = PriceHistory(product_id=product.id, price=price, timestamp=datetime.utcnow())
                        session.add(history)
                        
                        # Ensure source
                        if not product.source:
                            product.source = "officedepot"
                        
                        if price < old_price and old_price > 0:
                             drop_amount = old_price - price
                             drop_pct = (drop_amount / old_price) * 100
                             
                             # Usar configuración global en lugar de hardcode
                             min_pct = SEARCH_CONFIG.get("min_price_drop_percent", 50) # Fallback to 50 if somehow missing
                             min_amount = SEARCH_CONFIG.get("min_price_drop_amount", 5000)
                             
                             if drop_pct >= min_pct or drop_amount >= min_amount:
                                 alerts.append({
                                    "source": "officedepot",
                                    "title": product.name,
                                    "price": price,
                                    "old_price": old_price,
                                    "discount_pct": round(drop_pct, 1),
                                    "url": product.url
                                })
                    
                    product.last_checked = datetime.utcnow()
                    session.commit()
                    
            except Exception as e:
                logger.error(f"Error actualizando producto {product.name}: {e}")
                
    except Exception as e:
         logger.error(f"Error general en update_tracked_products_officedepot: {e}")
    finally:
         session.close()

    return alerts
