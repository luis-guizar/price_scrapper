import requests
import os
import json
import logging
from dotenv import load_dotenv

#Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)

# Leemos las variables de entorno
API_KEY = os.getenv("KEEPA_API_KEY")
DOMAIN = os.getenv("AMAZON_DOMAIN_ID")


def clean_payload(payload):
    """Elimina las llaves vacías o con valor -1 que confunden a la API"""
    logger.debug(f"Limpiando payload con {len(payload)} claves originales")
    clean = {}
    removed_count = 0
    
    for k, v in payload.items():
        # Regla 1: Si es lista vacía, ignorar
        if isinstance(v, list) and len(v) == 0:
            logger.debug(f"  Removiendo '{k}': lista vacía")
            removed_count += 1
            continue
        # Regla 2: Si es -1 (como minRating), ignorar
        if v == -1:
            logger.debug(f"  Removiendo '{k}': valor -1")
            removed_count += 1
            continue
        # Regla 3: Si es lista con -1 (como salesRankRange [-1, -1]), ignorar
        if isinstance(v, list) and len(v) == 2 and v[0] == -1 and v[1] == -1:
            logger.debug(f"  Removiendo '{k}': lista [-1, -1]")
            removed_count += 1
            continue
        
        clean[k] = v
    
    logger.info(f"Payload limpiado: {removed_count} claves removidas, {len(clean)} claves restantes")
    return clean

def get_keepa_deals():
    logger.info("Iniciando escaneo de Keepa API...")
    # URL Base (Dirección de envío)
    url_post = f"https://api.keepa.com/deal?key={API_KEY}"
    logger.debug(f"Endpoint: {url_post[:50]}...")
    
    # EL JSON "SUCIO" ORIGINAL
    dirty_json = {
        "page": 0, "domainId": DOMAIN, 
        "excludeCategories": [], "includeCategories": [],
        "priceTypes": [0], "deltaRange": [0, 2147483647],
        "deltaPercentRange": [60, 2147483647], # >60%
        "salesRankRange": [-1, -1], "currentRange": [0, 2147483647],
        "minRating": -1, "isLowest": False, "isLowest90": False,
        "isLowestOffer": False, "isOutOfStock": False, "titleSearch": "",
        "isRangeEnabled": True, "isFilterEnabled": True, "filterErotic": False,
        "singleVariation": False, "hasReviews": False, "isPrimeExclusive": False,
        "mustHaveAmazonOffer": False, "mustNotHaveAmazonOffer": False,
        "sortType": 1, "dateRange": "4", "warehouseConditions": [2, 3, 4, 5],
        "isRisers": False, "isHighest": False, "hasAmazonOffer": True,
        "salesRankDisplayGroup": [], "websiteDisplayGroupName": [], "websiteDisplayGroup": [],
        "type": [], "manufacturer": [], "brand": [], "brandStoreName": [],
        "brandStoreUrlName": [], "productGroup": [], "model": [], "color": [],
        "size": [], "unitType": [], "scent": [], "itemForm": [], "pattern": [],
        "style": [], "material": [], "itemTypeKeyword": [], "targetAudienceKeyword": [],
        "edition": [], "format": [], "author": [], "binding": [], "languages": [],
        "partNumber": []
    }
    
    final_payload = clean_payload(dirty_json)

    logger.info(f"📡 Enviando payload limpio a Keepa API...")

    try:
        # 2. ENVÍO (Usamos json=... para que requests lo maneje igual que en el debug)
        response = requests.post(url_post, json=final_payload, timeout=15)
        logger.debug(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                logger.error(f"❌ Error API Keepa: {data['error']}")
                return []

            tokens_left = data.get("tokensLeft", 0)
            logger.info(f"💰 Tokens restantes en Keepa: {tokens_left}")
            
            if "deals" in data and "dr" in data["deals"]:
                deals_count = len(data["deals"]["dr"])
                logger.info(f"📊 Se encontraron {deals_count} deals en Keepa")
                parsed = parse_deals(data["deals"]["dr"])
                logger.info(f"✅ Se parsearon {len(parsed)} deals que pasaron filtros")
                return parsed
            else:
                logger.info("✅ Éxito (200 OK) - No hay ofertas >60% ahora mismo.")
                return []
        else:
            logger.error(f"❌ Error HTTP {response.status_code}")
            logger.debug(f"Response: {response.text[:500]}")
            return []

    except requests.exceptions.Timeout:
        logger.error("❌ Timeout al conectar con Keepa")
        return []
    except Exception as e:
        logger.exception(f"❌ Excepción inesperada en Keepa: {e}")
        return []

def parse_deals(deals_list, min_discount=70):
    clean_deals = []
    rejected_count = 0
    
    logger.info(f"Parseando {len(deals_list)} deals con descuento mínimo de {min_discount}%")
    
    for i, deal in enumerate(deals_list):
        try:
            asin = deal.get('asin', 'UNKNOWN')
            title = deal.get('title', 'Sin título')
            
            # 1. Identificar el precio actual (Priorizamos Buy Box [7], luego Amazon [0])
            current_prices = deal.get('current', [])
            
            # Usamos el índice 7 (Buy Box) si existe, si no el 0 (Amazon)
            idx = 7 if (len(current_prices) > 7 and current_prices[7] > 0) else 0
            
            curr_price_int = current_prices[idx]
            if curr_price_int <= 0:
                logger.debug(f"  [{i}] {asin}: Sin precio válido")
                rejected_count += 1
                continue # Sin precio válido
            
            # 2. Identificar el promedio de 90 días para ese MISMO índice
            # avg[0] es el bloque de 90 días según Keepa
            avg_data = deal.get('avg', [])
            if not avg_data or not isinstance(avg_data[0], list):
                logger.debug(f"  [{i}] {asin}: Sin datos de promedio")
                rejected_count += 1
                continue
                
            avg_90_price_int = avg_data[0][idx]
            
            # Si el promedio es -2 o -1, significa que no hay datos suficientes
            if avg_90_price_int <= 0:
                logger.debug(f"  [{i}] {asin}: Promedio inválido")
                rejected_count += 1
                continue

            # 3. Cálculos finales
            final_price = curr_price_int / 100.0
            final_avg = avg_90_price_int / 100.0
            
            # El descuento se calcula sobre el promedio histórico
            pct_off = int(((final_avg - final_price) / final_avg) * 100)

            if pct_off >= min_discount:
                deal_obj = {
                    "title": title,
                    "price": round(final_price, 2),
                    "avg_90": round(final_avg, 2),
                    "discount_pct": pct_off,
                    "url": f"https://www.amazon.com.mx/dp/{asin}",
                    "asin": asin,
                    "type": "Buy Box" if idx == 7 else "Amazon"
                }
                clean_deals.append(deal_obj)
                logger.info(f"  ✅ [{i}] {asin}: {pct_off}% OFF - ${final_price}")
            else:
                logger.debug(f"  [{i}] {asin}: {pct_off}% (menos del mínimo {min_discount}%)")
                rejected_count += 1
                
        except (IndexError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"  [{i}] Error parseando deal: {e}")
            rejected_count += 1
            continue

    # Ordenar por el mejor descuento
    sorted_deals = sorted(clean_deals, key=lambda x: x['discount_pct'], reverse=True)
    logger.info(f"Resultado final: {len(sorted_deals)} deals válidos, {rejected_count} rechazados")
    return sorted_deals
