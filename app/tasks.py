from app.celery_app import app
from app.keepa_service import get_keepa_deals
from app.promodescuentos_service import get_promodescuentos_deals
from app.officedepot_service import get_officedepot_deals, update_tracked_products_officedepot
from app.cyberpuerta_service import get_cyberpuerta_deals
from app.chedraui_service import get_chedraui_deals


import requests
import os
import redis
import logging
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)

# Monitor system
from app.monitoring import Monitor
monitor = Monitor()

# Usamos Redis para no repetir alertas del mismo producto cada 10 min
redis_client = redis.Redis(host='redis', port=6379, db=1)

def send_telegram_alert(deal):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        logger.error("❌ Variables de entorno TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no configuradas")
        return False
    
    source = deal.get('source', 'keepa')
    
    # Formato diferente según la fuente
    if source == 'promodescuentos':
        msg = (
            f"🔥 ¡OFERTA DETECTADA EN PROMODESCUENTOS! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Precio: ${deal['price']}\n"
            f"🌡️ Popularidad: {deal.get('temperature_level', 'N/A')}\n"
            f"🔗 {deal.get('url', '')}"
        )
    elif source == 'officedepot':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN OFFICE DEPOT! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'cyberpuerta':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN CYBERPUERTA! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )

    elif source == 'walmart':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN WALMART! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
            f"🔗 {deal['url']}"
        )
    elif source == 'chedraui':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN CHEDRAUI! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    else:  # keepa
        msg = (
            f"🔥 ¡OFERTA REAL DETECTADA EN AMAZON! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Precio Actual: ${deal['price']}\n"
            f"📉 Promedio 90 días: ${deal.get('avg_90', deal.get('avg_price', 'N/A'))}\n"
            f"🔗 {deal['url']}"
        )
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg},
            timeout=5
        )
        if response.status_code == 200:
            logger.info(f"✅ Alerta enviada a Telegram: {deal['title'][:50]}")
            return True
        else:
            logger.error(f"❌ Error enviando alerta Telegram: {response.status_code}")
            return False
    except Exception as e:
        logger.exception(f"❌ Excepción enviando alerta: {e}")
        return False

@app.task
def scan_amazon_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_amazon_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        deals = get_keepa_deals()
        
        if not deals:
            logger.warning("❌ No se encontraron ofertas en Keepa")
            monitor.record_no_deals('keepa')
            return
        
        monitor.record_found_deals('keepa')
        
        # --- FILTRO ANTI-SPAM ---
        deals = deals[:10]  # Top 10 ofertas
        
        logger.info(f"📊 Procesando TOP {len(deals)} ofertas de Keepa...")

        alerted_count = 0
        skipped_count = 0
        
        for deal in deals:
            asin = deal['asin']
            title = deal['title'][:50]
            price = deal['price']
            discount = deal['discount_pct']
            
            # Filtro de precio mínimo
            if price < 200:
                logger.debug(f"  ⏭️ {asin}: Precio muy bajo (${price})")
                skipped_count += 1
                continue

            cache_key = f"alerted:keepa:{asin}"
            if not redis_client.get(cache_key):
                logger.info(f"  🔔 Alertando: {discount}% OFF - {title}")
                if send_telegram_alert(deal):
                    redis_client.setex(cache_key, 86400, "1")
                    alerted_count += 1
            else:
                logger.debug(f"  ✋ {asin}: Ya alertado recientemente")
                skipped_count += 1
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_amazon_deals: {e}")
        monitor.record_failure('keepa', str(e))
    finally:
        logger.info("=" * 60)

@app.task
def scan_promodescuentos_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_promodescuentos_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        deals = get_promodescuentos_deals(page=1)
        
        if not deals:
            logger.warning("❌ No se encontraron ofertas en PromoDescuentos")
            monitor.record_no_deals('promodescuentos')
            return
        
        monitor.record_found_deals('promodescuentos')
        
        # Tomar solo los mejores (por temperatura/popularidad)
        deals = deals[:10]
        
        logger.info(f"📊 Procesando TOP {len(deals)} ofertas de PromoDescuentos...")
        
        alerted_count = 0
        skipped_count = 0
        
        for deal in deals:
            thread_id = deal['thread_id']
            title = deal['title'][:50]
            discount = deal['discount_pct']
            temp_level = deal.get('temperature_level', 'N/A')
            
            cache_key = f"alerted:promodesc:{thread_id}"
            
            if not redis_client.get(cache_key):
                logger.info(f"  🔔 Alertando: {discount}% OFF [{temp_level}] - {title}")
                if send_telegram_alert(deal):
                    redis_client.setex(cache_key, 43200, "1")  # 12 horas
                    alerted_count += 1
            else:
                logger.debug(f"  ✋ {thread_id}: Ya alertado recientemente")
                skipped_count += 1
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_promodescuentos_deals: {e}")
        monitor.record_failure('promodescuentos', str(e))
    finally:
        logger.info("=" * 60)

@app.task
def scan_officedepot_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_officedepot_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        deals, processed_urls = get_officedepot_deals()
        
        # Add targeted products, skipping ones already processed
        targeted_deals = update_tracked_products_officedepot(exclude_urls=processed_urls)
        if targeted_deals:
             deals.extend(targeted_deals)
        
        if not deals:
            logger.info("ℹ️ No se detectaron bajadas de precio significativas en Office Depot!!")
            monitor.record_no_deals('officedepot')
            return

        monitor.record_found_deals('officedepot')
        
        logger.info(f"📊 Procesando {len(deals)} alertas de precio de Office Depot...")
        
        alerted_count = 0
        skipped_count = 0
        
        for deal in deals:
            try:
                # Usar el SKU o URL como clave única para no alertar lo mismo repetidamente
                unique_id = deal.get('sku') or deal.get('url')
                if not unique_id:
                    continue

                cache_key = f"alerted:officedepot:{unique_id}"

                if not redis_client.get(cache_key):
                    logger.info(f"  🔔 Alertando: {deal['title']}")
                    if send_telegram_alert(deal):
                        # Cachear por 24 horas para evitar repeticiones
                        redis_client.setex(cache_key, 86400, "1")
                        alerted_count += 1
                else:
                    logger.info(f"  ✋ {deal['title']} ({unique_id}): Ya alertado recientemente - SKIPPING")
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error enviando alerta individual: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas enviadas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_officedepot_deals: {e}")
        monitor.record_failure('officedepot', str(e))
    finally:
        logger.info("=" * 60)

@app.task
def scan_cyberpuerta_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_cyberpuerta_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        alerts, count = get_cyberpuerta_deals()
        
        if not alerts:
            logger.info(f"ℹ️ No se detectaron bajadas de precio significativas en Cyberpuerta ({count} productos procesados)")
            monitor.record_no_deals('cyberpuerta')
            return

        monitor.record_found_deals('cyberpuerta')
        
        logger.info(f"📊 Procesando {len(alerts)} alertas de precio de Cyberpuerta...")
        
        alerted_count = 0
        skipped_count = 0
        
        for deal in alerts:
            try:
                unique_id = deal.get('sku') or deal.get('url')
                if not unique_id:
                    continue

                cache_key = f"alerted:cyberpuerta:{unique_id}"

                if not redis_client.get(cache_key):
                    logger.info(f"  🔔 Alertando: {deal['title']}")
                    if send_telegram_alert(deal):
                        redis_client.setex(cache_key, 86400, "1")  # 24 horas
                        alerted_count += 1
                        import time
                        time.sleep(1)  # Rate limit Telegram API
                else:
                    logger.info(f"  ✋ {deal['title']} ({unique_id}): Ya alertado recientemente - SKIPPING")
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error enviando alerta individual Cyberpuerta: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas enviadas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_cyberpuerta_deals: {e}")
        monitor.record_failure('cyberpuerta', str(e))
    finally:
        logger.info("=" * 60)

@app.task
def scan_chedraui_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_chedraui_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        alerts, count = get_chedraui_deals()
        
        if not alerts:
            logger.info(f"ℹ️ No se detectaron bajadas de precio significativas en Chedraui ({count} productos procesados)")
            monitor.record_no_deals('chedraui')
            return

        monitor.record_found_deals('chedraui')
        
        logger.info(f"📊 Procesando {len(alerts)} alertas de precio de Chedraui...")
        
        alerted_count = 0
        skipped_count = 0
        
        for deal in alerts:
            try:
                unique_id = deal.get('sku') or deal.get('url')
                if not unique_id:
                    continue

                cache_key = f"alerted:chedraui:{unique_id}"

                if not redis_client.get(cache_key):
                    logger.info(f"  🔔 Alertando: {deal['title']}")
                    if send_telegram_alert(deal):
                        redis_client.setex(cache_key, 86400, "1")  # 24 horas
                        alerted_count += 1
                        import time
                        time.sleep(1)  # Rate limit Telegram API
                else:
                    logger.info(f"  ✋ {deal['title']} ({unique_id}): Ya alertado recientemente - SKIPPING")
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error enviando alerta individual Chedraui: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas enviadas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_chedraui_deals: {e}")
        monitor.record_failure('chedraui', str(e))
    finally:
        logger.info("=" * 60)
