import requests
import os
import logging
import redis
import time
from datetime import datetime
from app.models import SessionLocal, Product
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Configurar logging
logger = logging.getLogger(__name__)

# Configuración de Redis
redis_client = redis.Redis(host='redis', port=6379, db=1)

# Constantes API
BASE_URL = "https://api.mercadolibre.com"
AUTH_URL = "https://api.mercadolibre.com/oauth/token"
SITE_ID = "MLM"

def get_auth_token():
    """
    Obtiene el access_token de Redis o lo solicita a la API si no existe/expiró.
    """
    token_key = "meli_access_token"
    token = redis_client.get(token_key)

    if token:
        # logger.debug("🔑 Usando token de Mercado Libre desde cache")
        return token.decode('utf-8')

    logger.info("🔄 Solicitando nuevo token a Mercado Libre...")
    
    client_id = os.getenv("MELI_CLIENT_ID")
    client_secret = os.getenv("MELI_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.error("❌ Credenciales MELI_CLIENT_ID o MELI_CLIENT_SECRET no configuradas")
        return None

    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        response = requests.post(AUTH_URL, data=data, timeout=10)
        response.raise_for_status()
        
        auth_data = response.json()
        access_token = auth_data["access_token"]
        expires_in = auth_data["expires_in"]
        
        # Guardar en Redis con un buffer de 5 minutos para evitar condiciones de carrera
        ttl = max(expires_in - 300, 60)
        redis_client.setex(token_key, ttl, access_token)
        
        logger.info(f"✅ Nuevo token obtenido. Expira en {expires_in} segundos.")
        return access_token

    except Exception as e:
        logger.error(f"❌ Error obteniendo token de Mercado Libre: {e}")
        return None

def get_headers(token=None):
    if not token:
        token = get_auth_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

from bs4 import BeautifulSoup
import json

# ... (rest of imports)

def search_products(keywords, sort_by='relevancia', free_shipping=False):
    """
    Busca productos usando Scraping en listado.mercadolibre.com.mx
    debido a bloqueos 403 en la API de sites/MLM/search.
    """
    processed_products = []
    session = SessionLocal()
    
    # Headers para simular navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-419,es;q=0.9",
        "Referer": "https://www.mercadolibre.com.mx/"
    }

    try:
        for keyword in keywords:
            logger.info(f"🔎 Scraping Mercado Libre: '{keyword}'")
            
            # Construir URL de busqueda web
            # Ejemplo: https://listado.mercadolibre.com.mx/iphone-15_NoIndex_True#D[A:iphone%2015,on]
            # Formato simple: https://listado.mercadolibre.com.mx/termino-busqueda
            fmt_keyword = keyword.replace(" ", "-")
            url = f"https://listado.mercadolibre.com.mx/{fmt_keyword}"
            
            # Añadir filtros si es posible, aunque por URL es mas complejo mapearlos todos igual que la API.
            # Por simplicidad, buscamos y luego filtramos o procesamos lo que llega.
            # El ordenamiento se puede pasar por query param a veces, pero por scraping básico vamos al default.
            
            if sort_by == 'barato':
               url += "_OrderId_PRICE_ASC"

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Estrategia: Buscar items en el DOM
                # Las clases de ML cambian, pero suelen tener 'ui-search-layout__item'
                items = soup.find_all('li', class_='ui-search-layout__item')
                
                if not items:
                     # Intentar otra clase comun
                     items = soup.find_all('div', class_='ui-search-result__wrapper')

                logger.info(f"   -> Encontrados {len(items)} items HTML para '{keyword}'")

                for i, item in enumerate(items):
                    try:
                        # Debug structure for first item
                        if i == 0:
                             logger.info(f"DEBUG HTML Item 0 class: {item.get('class')}")
                             # logger.info(f"DEBUG HTML Item 0 content: {str(item)[:200]}")

                        # Extraer link
                        link_tag = item.find('a', class_='ui-search-link')
                        if not link_tag: 
                            # Intentar buscar polyfill_nc (otra clase de ML)
                            link_tag = item.find('a', class_='ui-search-result__content')
                            
                        if not link_tag:
                             # Ultimo intento, cualquier A con href
                             link_tag = item.find('a', href=True)
                        
                        if not link_tag:
                             if i < 3: logger.warning(f"⚠️ Skip item {i}: No se encontro link tag <a> en el item.")
                             continue
                             
                        permalink = link_tag.get('href', '')
                        # logger.info(f"DEBUG Link: {permalink[:30]}...")
                        
                        # Extraer titulo
                        title_tag = item.find('h2', class_='ui-search-item__title')
                        title = title_tag.get_text().strip() if title_tag else "Sin titulo"
                        
                        # Extraer precio
                        price_container = item.find('div', class_='ui-search-price__second-line')
                        price_val = 0.0
                        if price_container:
                            price_span = price_container.find('span', class_='andes-money-amount__fraction')
                            if price_span:
                                price_val = float(price_span.get_text().replace('.', '').replace(',', '.')) # Cuidado con separadores
                                # ML usa punto para miles en MX? o coma? 
                                # En MX es coma para miles, punto para decimales?
                                # Usualmente en HTML viene "20,000" (veinte mil).
                                # Vamos a limpiar todo lo que no sea digito
                                txt = price_span.get_text()
                                # Limpieza basica: quitar puntos y comas y convertir
                                # Mejor estrategia: ver si hay decimales
                                # Asumimos entero por ahora si es complejo parsear
                                pass

                        # Re-parseo precio mas robusto
                        # Buscamos el meta price si existe o el texto plano
                        # ML suele poner <span class="andes-money-amount__fraction" aria-hidden="true">4,999</span>
                        if price_val == 0:
                             price_tag = item.find('span', class_='andes-money-amount__fraction')
                             if price_tag:
                                 txt_price = price_tag.get_text().replace(',', '')
                                 try:
                                     price_val = float(txt_price)
                                 except:
                                     pass

                        # ID: Extraer de la URL o input hidden
                        # https://articulo.mercadolibre.com.mx/MLM-123456-...
                        # ID suele ser MLM-123456
                        ml_id = None
                        if 'MLM' in permalink:
                            import re
                            match = re.search(r'(MLM-?\d+)', permalink)
                            if match:
                                ml_id = match.group(1).replace('-', '') # MLM12345

                        if not ml_id:
                            # Intentar buscar en un input name="item_id"
                            # logger.debug(f"⚠️ Saltando item sin ID MLM: {permalink[:50]}...")
                            continue 
                            
                        # Guardar en DB
                        db_product = session.query(Product).filter(
                             or_(Product.sku == ml_id, Product.url == permalink)
                        ).first()

                        if db_product:
                             # logger.debug(f"Item existente: {ml_id} - ${price_val}")
                             if abs(db_product.current_price - price_val) > 0.1 and price_val > 0:
                                 db_product.current_price = price_val
                             if not db_product.sku:
                                 db_product.sku = ml_id
                             db_product.last_checked = datetime.utcnow()
                        else:
                             if price_val > 0:
                                # logger.debug(f"Item nuevo: {ml_id} - ${price_val}")
                                new_product = Product(
                                    name=title,
                                    sku=ml_id,
                                    url=permalink,
                                    current_price=price_val,
                                    original_price=None, # Dificil sacar orig price facil sin entrar al item
                                    last_checked=datetime.utcnow()
                                )
                                session.add(new_product)
                             else:
                                # logger.debug(f"⚠️ Saltando item {ml_id} con precio 0")
                                pass
                        
                        processed_products.append({
                            "id": ml_id,
                            "title": title,
                            "price": price_val,
                            "url": permalink
                        })

                    except Exception as e:
                        logger.error(f"Error parseando item HTML: {e}")
                        continue

                session.commit()

            except Exception as e:
                logger.error(f"❌ Error scraping '{keyword}': {e}")
                session.rollback()
                
    except Exception as e:
        logger.error(f"❌ Error general en search_products scraping: {e}")
    finally:
        session.close()

    return processed_products

def update_tracked_products():
    """
    Batch update de productos MLM rastreados en la BD.
    AHORA USANDO SCRAPING POR PRODUCTO para evitar bloqueos API (401/403).
    """
    updates = []
    session = SessionLocal()
    
    try:
        # Obtener todos los productos MLM
        ml_products = session.query(Product).filter(Product.sku.like("MLM%")).all()
        
        if not ml_products:
            logger.info("ℹ️ No hay productos de Mercado Libre para monitorear.")
            return []

        logger.info(f"🔄 Monitoreando {len(ml_products)} productos de Mercado Libre (Scraping Paralelo)...")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def scrape_single_product(product_id, url, old_price, product_name, current_original_price):
            result = None
            try:
                if not url: return None
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Referer": "https://www.mercadolibre.com.mx/"
                }

                # logger.debug(f"Checking {product_id}...")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 404:
                     return None # Borrado

                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                new_price = 0.0
                
                # 1. Intentar Meta Tag
                price_meta = soup.find("meta", property="product:price:amount")
                if price_meta:
                    try:
                        content = price_meta.get("content")
                        if content: new_price = float(content)
                    except: pass
                
                # 2. Intentar UI
                if new_price == 0:
                    price_container = soup.find("div", class_="ui-pdp-price__second-line")
                    if price_container:
                        fraction = price_container.find("span", class_="andes-money-amount__fraction")
                        if fraction:
                             txt = fraction.get_text().replace(',', '')
                             try: new_price = float(txt)
                             except: pass
                
                if new_price > 0:
                    return {
                        "id": product_id,
                        "new_price": new_price,
                        "old_price": old_price,
                        "name": product_name,
                        "url": url,
                        "original_price": current_original_price
                    }
            except Exception as e:
                # logger.error(f"Error scraping {product_id}: {e}")
                pass
            return None

        # Usar ThreadPool para paralelizar
        max_workers = 8
        updates = []
        
        # Preparamos datos para no pasar objetos de session al thread
        products_data = []
        for p in ml_products:
            products_data.append({
                "id": p.id,
                "sku": p.sku,
                "url": p.url,
                "current_price": p.current_price,
                "name": p.name,
                "original_price": p.original_price
            })

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_sku = {
                executor.submit(
                    scrape_single_product, 
                    p["sku"], p["url"], p["current_price"], p["name"], p["original_price"]
                ): p["sku"] 
                for p in products_data
            }
            
            processed_count = 0
            for future in as_completed(future_to_sku):
                processed_count += 1
                sku = future_to_sku[future]
                try:
                    res = future.result()
                    if res:
                        # Actualizar en BD (necesitamos re-query o usar session local si fuera thread-safe, 
                        # pero mejor hacer update masivo o uno por uno en main thread)
                        # Hacemos update clean en main thread
                        
                        # Buscar producto en session actual para update
                        db_prod = session.query(Product).filter(Product.sku == sku).first()
                        if db_prod:
                            new_price = res["new_price"]
                            old_price = db_prod.current_price
                            
                            # Actualizar precio si varía
                            if abs(new_price - old_price) > 0.1:
                                db_prod.current_price = new_price
                                if new_price < old_price and old_price > 0:
                                    drop_pct = ((old_price - new_price) / old_price) * 100
                                    updates.append({
                                        "source": "mercadolibre",
                                        "title": db_prod.name,
                                        "price": new_price,
                                        "old_price": old_price,
                                        "discount_pct": round(drop_pct, 1),
                                        "url": db_prod.url,
                                        "sku": sku
                                    })
                            
                            db_prod.last_checked = datetime.utcnow()
                except Exception as exc:
                    logger.error(f"Generado error en thread {sku}: {exc}")
                
                # Commit cada tanto para no bloquear
                if processed_count % 50 == 0:
                    session.commit()
                    logger.info(f"   ...Procesados {processed_count}/{len(ml_products)}")

            session.commit() # Final commit

    except Exception as e:
        logger.error(f"❌ Error general en update_tracked_products: {e}")
    finally:
        session.close()

    return updates
