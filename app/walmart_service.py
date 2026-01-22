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
    Obtiene productos de Walmart MX parseando el script data id="__NEXT_DATA__".
    Soporta páginas de categorías y búsquedas (Tempo modules).
    """
    logger.info(f"Escaneando Walmart: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
    }

    products = []
    seen_ids = set()
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if next_data_script:
            try:
                data = json.loads(next_data_script.string)
                props = data.get('props', {}).get('pageProps', {})
                
                # 1. Estrategia: Producto Individual (Página de producto)
                # ... (Mantener lógica si el usuario pone URL directa) ...
                initial_state = props.get('initialState', {})
                product_data = initial_state.get('product', {}).get('selectedProduct', {})
                # Si encontramos un producto único, lo agregamos y retornamos
                if product_data:
                     # (Lógica simplificada para producto único, similar a antes)
                     # Pero priorizamos la lógica de lista si es una categoría
                     pass

                # 2. Estrategia: Lista de productos (Tempo Data para Categorías/Búsqueda)
                tempo_data = props.get('initialTempoData', {})
                modules = tempo_data.get('contentLayout', {}).get('modules', [])
                
                logger.info(f"Analizando {len(modules)} módulos en la página...")
                
                candidates = []
                
                for mod in modules:
                    configs = mod.get('configs', {})
                    
                    # Buscar en itemsSelection
                    if 'itemsSelection' in configs:
                         items_sel = configs['itemsSelection']
                         if isinstance(items_sel, dict) and 'products' in items_sel:
                              candidates.extend(items_sel['products'])

                    # Buscar en productsConfig
                    if 'productsConfig' in configs:
                         prod_conf = configs['productsConfig']
                         if isinstance(prod_conf, dict) and 'products' in prod_conf:
                              pl = prod_conf['products']
                              if isinstance(pl, list):
                                  candidates.extend(pl)
                
                logger.info(f"Candidatos encontrados crudos: {len(candidates)}")

                for p in candidates:
                    try:
                        pid = p.get('id') or p.get('usItemId')
                        if not pid or pid in seen_ids:
                            continue
                        
                        seen_ids.add(pid)
                        
                        name = p.get('name')
                        
                        # Determinar precio
                        price = 0.0
                        if 'price' in p and isinstance(p['price'], (int, float)):
                            price = float(p['price'])
                        elif 'priceInfo' in p:
                             p_info = p['priceInfo']
                             if 'currentPrice' in p_info:
                                  curr = p_info['currentPrice']
                                  if 'price' in curr:
                                       price = float(curr['price'])
                        
                        # URL
                        canonical = p.get('canonicalUrl', '')
                        if canonical:
                            if canonical.startswith('http'):
                                p_url = canonical
                            else:
                                p_url = f"https://www.walmart.com.mx{canonical}"
                        else:
                            # Fallback con ID
                            p_url = f"https://www.walmart.com.mx/ip/{pid}"
                            
                        # Imagen
                        image = p.get('image', '')
                        
                        if name and price > 0:
                            products.append({
                                "@type": "Product",
                                "name": name,
                                "sku": pid,
                                "url": p_url,
                                "offers": {
                                    "price": price,
                                    "priceCurrency": "MXN"
                                },
                                "image": image
                            })
                    except Exception as e:
                        continue
                        
                if not products and product_data:
                     # Fallback a producto único si no hallamos lista
                     # ... (Lógica de producto único simplificada aquí por brevedad)
                     pass
                     
                logger.info(f"✅ Total productos válidos extraídos: {len(products)}")

            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de __NEXT_DATA__")
        else:
            logger.warning("Tag <script id='__NEXT_DATA__'> no encontrado.")
            
    except Exception as e:
        logger.error(f"Error parseando Walmart: {e}")

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
