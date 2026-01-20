import json
import re
import logging
from datetime import datetime
import requests

# Configurar logging
logger = logging.getLogger(__name__)

# ==================== PARÁMETROS DE FILTRACIÓN ====================
# Puedes ajustar estos valores según tus necesidades
FILTER_CONFIG = {
    "min_discount": 60,           # Descuento mínimo (%) - bajado de 30
    "min_price": 100,              # Precio mínimo (MXN) - bajado de 100
    "max_price": 100000,          # Precio máximo (MXN) - subido de 50000
    "excluded_keywords": [
        "gratis", "free", "no price", 
        "kindle", "ebook", "libro digital"  # Excluir tipos de producto
    ],
    "min_temperature": 100,        # Temperatura mínima - bajado de 100
    "allowed_merchants": None,    # None = todos, o lista: ["Walmart", "Amazon", "Mercado Libre"]
}

# Frecuencia de escaneo (en segundos)
# En Celery Beat se configura en celerybeat-schedule
SCAN_FREQUENCY_SECONDS = 60  # 10 minutos

def fetch_promodescuentos_deals(page=1):
    """
    Obtiene las ofertas de www.promodescuentos.com/nuevas
    Retorna lista de ofertas parseadas
    """
    url = "https://www.promodescuentos.com/nuevas"
    logger.info(f"Conectando a PromoDescuentos (página {page})...")
    logger.debug(f"URL: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    logger.debug(f"HTTP Status: {response.status_code}")
    
    logger.debug("Buscando datos de ofertas en atributos data-vue3...")
    
    deals = []
    # Expresión regular para encontrar el contenido de data-vue3
    vue3_data_matches = re.findall(r"data-vue3='(.*?)'", response.text)
    
    for vue3_data_str in vue3_data_matches:
        try:
            # El contenido de data-vue3 es un JSON
            vue3_json = json.loads(vue3_data_str)
            
            # Nos interesan los componentes que normalizan la data de cada 'thread'
            if vue3_json.get('name') == 'ThreadMainListItemNormalizer':
                thread_data = vue3_json.get('props', {}).get('thread')
                if thread_data:
                    deals.append(thread_data)
        except json.JSONDecodeError:
            # Ignorar si el contenido del atributo no es un JSON válido
            logger.debug(f"No se pudo parsear un atributo data-vue3 a JSON: {vue3_data_str[:100]}...")
            continue
    
    if deals:
        logger.info(f"✅ Se extrajeron {len(deals)} ofertas crudas de PromoDescuentos")
    else:
        logger.warning("❌ No se encontraron ofertas con el nuevo método de extracción (data-vue3).")

    return deals

def filter_deals(deals_raw):
    """
    Filtra ofertas según los parámetros definidos en FILTER_CONFIG
    """
    logger.info(f"Filtrando {len(deals_raw)} ofertas crudas...")
    logger.debug(f"Filtros: min_discount={FILTER_CONFIG['min_discount']}%, "
                f"price_range=[${FILTER_CONFIG['min_price']}, ${FILTER_CONFIG['max_price']}], "
                f"min_temp={FILTER_CONFIG['min_temperature']}")
    
    filtered = []
    rejected_reasons = {"type": 0, "keywords": 0, "discount": 0, "price": 0, "temperature": 0}
    
    for i, deal in enumerate(deals_raw):
        title = deal.get('title', '').lower()
        price = deal.get('price')
        temperature = deal.get('temperature', 0)

        # --- Validaciones básicas ---
        if deal.get('type') != 'Deal':
            rejected_reasons["type"] += 1
            continue
            
        if any(keyword in title for keyword in FILTER_CONFIG['excluded_keywords']):
            logger.debug(f"  [{i}] Rechazado por palabra clave: {title[:50]}")
            rejected_reasons["keywords"] += 1
            continue

        # --- Validaciones de oferta ---
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            rejected_reasons["price"] += 1
            continue
        
        if not (FILTER_CONFIG['min_price'] <= price <= FILTER_CONFIG['max_price']):
            logger.debug(f"  [{i}] Rechazado por precio ${price}: {title[:50]}")
            rejected_reasons["price"] += 1
            continue
        
        # Validar descuento
        discount = deal.get('priceDiscount')
        if discount is None:
            next_best_price = deal.get('nextBestPrice')
            if next_best_price and isinstance(next_best_price, (int, float)) and next_best_price > price:
                discount = (1 - (price / next_best_price)) * 100
            else:
                discount = 0
        
        if discount < FILTER_CONFIG['min_discount']:
            rejected_reasons["discount"] += 1
            continue
        
        if temperature < FILTER_CONFIG['min_temperature']:
            rejected_reasons["temperature"] += 1
            continue
        
        # Si pasó todos los filtros, agregar
        logger.debug(f"  ✅ [{i}] Aceptado ({int(discount)}%): {title[:50]}")
        filtered.append(deal)
    
    logger.info(f"Resultado filtrado: {len(filtered)} ofertas válidas")
    logger.info(f"Rechazados por: type={rejected_reasons['type']}, "
                f"keywords={rejected_reasons['keywords']}, "
                f"discount={rejected_reasons['discount']}, "
                f"price={rejected_reasons['price']}, "
                f"temp={rejected_reasons['temperature']}")
    
    return filtered

def parse_promodescuentos_deals(filtered_deals):
    """
    Convierte los deals filtrados al formato estándar
    """
    logger.info(f"Parseando {len(filtered_deals)} ofertas filtradas...")
    parsed = []
    errors = 0
    
    for i, deal in enumerate(filtered_deals):
        try:
            price = deal.get('price', 0)
            next_best = deal.get('nextBestPrice')
            discount_pct = deal.get('priceDiscount') # Can be None
            title = deal.get('title', 'Sin título')
            thread_id = deal.get('threadId', '?')
            
            if discount_pct is None:
                if next_best and isinstance(next_best, (int, float)) and next_best > price:
                    discount_pct = (1 - (price / next_best)) * 100
                else:
                    discount_pct = 0

            # Calcular el precio promedio (aproximado) si existe mejor precio
            if next_best and next_best > 0:
                avg_price = (price + next_best) / 2
            else:
                avg_price = price * (1 + discount_pct / 100)  # Estimación
            
            title_slug = deal.get('titleSlug')
            shareable_link = deal.get('shareableLink')

            # Construct URL
            url = ""
            if title_slug and thread_id:
                url = f"https://www.promodescuentos.com/ofertas/{title_slug}-{thread_id}"
            elif shareable_link:
                url = shareable_link
            else:
                url = f"https://www.promodescuentos.com/ofertas/{thread_id}" # Fallback
            
            parsed_deal = {
                "source": "promodescuentos",
                "title": title,
                "price": price,
                "avg_price": round(avg_price, 2),
                "discount_pct": int(discount_pct),
                "url": url,
                "thread_id": thread_id,
                "temperature": deal.get('temperature', 0),
                "temperature_level": deal.get('temperatureLevel', ''),
                "merchant_id": deal.get('merchantId'),
                "image_url": build_image_url(deal.get('mainImage', {})),
                "timestamp": datetime.now().isoformat(),
            }
            parsed.append(parsed_deal)
            logger.debug(f"  ✅ [{i}] {int(discount_pct)}% OFF - {title[:50]}")
            
        except (KeyError, TypeError) as e:
            logger.warning(f"  ⚠️ [{i}] Error parseando deal: {e}")
            errors += 1
            continue
    
    # Ordenar por descuento (mayor primero)
    sorted_deals = sorted(parsed, key=lambda x: x['discount_pct'], reverse=True)
    logger.info(f"Parseado: {len(sorted_deals)} deals válidos, {errors} errores")
    return sorted_deals

def build_image_url(image_data):
    """
    Construye la URL de imagen basada en la estructura de promodescuentos
    """
    if not image_data:
        return ""
    
    path = image_data.get('path', '')
    name = image_data.get('name', '')
    
    if path and name:
        return f"https://d2r9epyceweg5n.cloudfront.net/{path}/{name}_330x330.jpg"
    return ""

def get_promodescuentos_deals(page=1):
    """
    Pipeline completo: obtiene, filtra y parsea ofertas
    """
    logger.info(f"========== ESCANEO PROMODESCUENTOS INICIADO (página {page}) ==========")
    start_time = datetime.now()
    
    # 1. Obtener datos crudos
    raw_deals = fetch_promodescuentos_deals(page)
    if not raw_deals:
        logger.warning("Pipeline abortado: 0 ofertas obtenidas")
        return []
    
    # 2. Filtrar
    filtered_deals = filter_deals(raw_deals)
    
    if not filtered_deals:
        logger.warning("Pipeline abortado: 0 ofertas después del filtrado")
        return []
    
    # 3. Parsear
    final_deals = parse_promodescuentos_deals(filtered_deals)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"========== ESCANEO COMPLETADO EN {elapsed:.2f}s - {len(final_deals)} OFERTAS FINALES ==========")
    
    return final_deals
