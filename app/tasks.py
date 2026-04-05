from app.celery_app import app
from app.keepa_service import get_keepa_deals
from app.promodescuentos_service import get_promodescuentos_deals
from app.officedepot_service import get_officedepot_deals, update_tracked_products_officedepot
from app.cyberpuerta_service import get_cyberpuerta_deals
from app.chedraui_service import get_chedraui_deals
from app.elektra_service import get_elektra_deals



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

# DB Imports
from app.crud import create_alert, prune_database
from app.models import SessionLocal


# Usamos Redis para no repetir alertas del mismo producto cada 10 min
redis_client = redis.Redis(host='redis', port=6379, db=1)

def send_telegram_alert(deal):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    high_priority_chat_id = os.getenv('TELEGRAM_HIGH_PRIORITY_CHAT_ID')
    
    if not token or not chat_id:
        logger.error("❌ Variables de entorno TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no configuradas")
        return False
        
    # Explicitly filter out 'venta internacional' products
    title = deal.get('title', '').lower()
    if 'venta internacional' in title:
        logger.info(f"🚫 Alert blocked: Contiene 'venta internacional' - {deal.get('title', '')}")
        return False

    source = deal.get('source', 'keepa')
    
    # Route high-discount alerts to priority chat
    HIGH_PRIORITY_PCT = 75
    discount = deal.get('discount_pct', 0)
    is_high_priority = discount >= HIGH_PRIORITY_PCT
    target_chat_id = high_priority_chat_id if (is_high_priority and high_priority_chat_id) else chat_id
    prefix = '🚨' if is_high_priority else '📉'
    
    # Formato diferente según la fuente
    if source == 'promodescuentos':
        msg = (
            f"{'🚨' if is_high_priority else '🔥'} ¡OFERTA DETECTADA EN PROMODESCUENTOS! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Precio: ${deal['price']}\n"
            f"🌡️ Popularidad: {deal.get('temperature_level', 'N/A')}\n"
            f"🔗 {deal.get('url', '')}"
        )
    elif source == 'officedepot':
        msg = (
            f"{prefix} ¡BAJADA DE PRECIO EN OFFICE DEPOT! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'cyberpuerta':
        msg = (
            f"{prefix} ¡BAJADA DE PRECIO EN CYBERPUERTA! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'chedraui':
        msg = (
            f"{prefix} ¡BAJADA DE PRECIO EN CHEDRAUI! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'elektra':
        msg = (
            f"{prefix} ¡BAJADA DE PRECIO EN ELEKTRA! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'coppel':
        msg = (
            f"{prefix} ¡BAJADA DE PRECIO EN COPPEL! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    else:  # keepa
        msg = (
            f"{'🚨' if is_high_priority else '🔥'} ¡OFERTA REAL DETECTADA EN AMAZON! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Precio Actual: ${deal['price']}\n"
            f"📉 Promedio 90 días: ${deal.get('avg_90', deal.get('avg_price', 'N/A'))}\n"
            f"🔗 {deal['url']}"
        )
    
    import time
    
    # Simple retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Rate limiting: Sleep 1s before each request to be safe (Telegram limit is ~30 msg/sec, but safe side)
            time.sleep(1)
            
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": target_chat_id, "text": msg},
                timeout=10  # Increased timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Alerta enviada a Telegram: {deal['title'][:50]}")
                
                # Guardar alerta en DB
                try:
                    db = SessionLocal()
                    alert_data = {
                        "price": deal.get('price'),
                        "previous_price": deal.get('old_price'),
                        "change_pct": deal.get('discount_pct'),
                        "source": source,
                        "url": deal.get('url'),
                        "title": deal.get('title'),
                        # "product_id": deal.get('product_id') # Si lo tenemos
                    }
                    create_alert(db, alert_data)
                    db.close()
                except Exception as db_e:
                    logger.error(f"Error guardando alerta en DB: {db_e}")
                    
                return True
            elif response.status_code == 429:
                # Rate limited by Telegram
                retry_after = int(response.json().get('parameters', {}).get('retry_after', 5))
                logger.warning(f"⚠️ Telegram Rate Limit. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            else:
                logger.error(f"❌ Error enviando alerta Telegram: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Timeout sending Telegram alert (Attempt {attempt+1}/{max_retries})")
            time.sleep(2)
        except Exception as e:
            logger.exception(f"❌ Excepción enviando alerta: {e}")
            return False
            
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

@app.task
def scan_elektra_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_elektra_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        alerts, count = get_elektra_deals()
        
        if not alerts:
            logger.info(f"ℹ️ No se detectaron bajadas de precio significativas en Elektra ({count} productos procesados)")
            monitor.record_no_deals('elektra')
            return

        monitor.record_found_deals('elektra')
        
        logger.info(f"📊 Procesando {len(alerts)} alertas de precio de Elektra...")
        
        alerted_count = 0
        skipped_count = 0
        
        for deal in alerts:
            try:
                unique_id = deal.get('sku') or deal.get('url')
                if not unique_id:
                    continue

                cache_key = f"alerted:elektra:{unique_id}"

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
                logger.error(f"Error enviando alerta individual Elektra: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas enviadas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_elektra_deals: {e}")
        monitor.record_failure('elektra', str(e))
    finally:
        logger.info("=" * 60)



@app.task
def scan_coppel_deals():
    """
    Dispatcher task: Reads all Coppel URLs and scrapes them sequentially.
    This saves massive amounts of RAM by reusing the same browser/context 
    and avoiding concurrent Playwright instances across celery workers.
    """
    logger.info("=" * 60)
    logger.info("🚀 TAREA INICIADA: scan_coppel_deals (Sequential Mode)")
    
    urls = []
    try:
        # Load URLs from file
        with open("coppel_urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)
    except FileNotFoundError:
        logger.error("coppel_urls.txt not found")
        return

    if not urls:
        logger.warning("No Coppel URLs found.")
        return

    logger.info(f"📅 Scanning {len(urls)} Coppel categories sequentially...")
    
    try:
        from app.coppel_service import CoppelService
        from app.crud import process_products
        from app.models import SessionLocal

        # The CoppelService already iterates over self.urls sequentially, 
        # effectively using 1 browser to load all categories and doing parallel pagination inside.
        service = CoppelService(urls) 
        products = service.run()
        
        if products:
            logger.info(f"✅ Found {len(products)} products total across categories, saving...")
            db = SessionLocal()
            try:
                process_products(products, db)
                monitor.record_found_deals('coppel')
                check_coppel_alerts(products, db)
            except Exception as e:
                logger.error(f"❌ DB Error: {e}")
            finally:
                db.close()
        else:
            logger.warning("⚠️ No products found in any Coppel category.")
            monitor.record_no_deals('coppel')
            
    except Exception as e:
        logger.error(f"❌ Coppel Scrape Failed: {e}")
        monitor.record_failure('coppel', str(e))
    finally:
        logger.info("=" * 60)


def check_coppel_alerts(products, db):
    """
    Helper to send alerts for a batch of products.
    Compares scraping price vs original_price (anchor) to find REAL drops.
    """
    from app.models import Product
    
    alerted_count = 0
    skipped_count = 0
    
    # Configuration for alerts
    MIN_DROP_PCT = 50
    
    for deal in products:
        try:
            current_price = float(deal.get('price', 0))
            sku = deal.get('sku')
            
            if current_price <= 0:
                continue
            
            # Find existing product in DB to compare price
            p_db = db.query(Product).filter(Product.sku == sku).first()
            if not p_db:
                # NO ALERTS for new products to avoid spam.
                continue
            
            if p_db.is_active is False:
                continue

            # Compare against original_price (anchor)
            anchor_price = p_db.original_price or p_db.current_price
            old_db_price = p_db.current_price
            
            # Only alert if price JUST dropped AND cumulative drop exceeds threshold
            if current_price < old_db_price and current_price < anchor_price:
                drop = anchor_price - current_price
                drop_pct = (drop / anchor_price) * 100
                
                if drop_pct >= MIN_DROP_PCT:
                    deal['discount_pct'] = round(drop_pct, 1)
                    deal['old_price'] = anchor_price
                    # Proceed to alert
                else:
                    continue
            else:
                # Price same or increased
                continue

            unique_id = deal.get('sku') or deal.get('url')
            if not unique_id: continue

            cache_key = f"alerted:coppel:{unique_id}"

            if not redis_client.get(cache_key):
                logger.info(f"  🔔 Alertando: {deal['name']}")
                deal['title'] = deal['name']
                
                if send_telegram_alert(deal):
                    redis_client.setex(cache_key, 86400, "1")  # 24 horas
                    alerted_count += 1
                    import time
                    time.sleep(1)
            else:
                skipped_count += 1

        except Exception as e:
            logger.error(f"Error checking alert: {e}")
            
    if alerted_count > 0:
        logger.info(f"✨ Sent {alerted_count} alerts for this category.")


@app.task
def cleanup_database_task():
    logger.info("=" * 60)
    logger.info("🧹 TAREA INICIADA: cleanup_database_task")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    db = SessionLocal()
    try:
        # Prune elements older than 30 days
        results = prune_database(db, days=30)
        
        logger.info(f"✅ Limpieza de DB completada en {(datetime.now() - start_time).total_seconds():.2f}s")
        logger.info(f"   - Productos eliminados (y su historial): {results.get('deleted_products', 0)}")
        logger.info(f"   - Alertas eliminadas: {results.get('deleted_alerts', 0)}")
        
    except Exception as e:
        logger.exception(f"❌ Error en cleanup_database_task: {e}")
        monitor.record_failure('cleanup_db', str(e))
    finally:
        db.close()
        logger.info("=" * 60)
