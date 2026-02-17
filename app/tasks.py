from app.celery_app import app
from app.keepa_service import get_keepa_deals
from app.promodescuentos_service import get_promodescuentos_deals
from app.officedepot_service import get_officedepot_deals, update_tracked_products_officedepot
from app.cyberpuerta_service import get_cyberpuerta_deals
from app.chedraui_service import get_chedraui_deals
from app.elektra_service import get_elektra_deals
from app.soriana_service import get_soriana_deals




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

    elif source == 'chedraui':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN CHEDRAUI! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'elektra':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN ELEKTRA! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'soriana':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN SORIANA! ({deal['discount_pct']}% OFF)\n\n"
            f"📦 {deal['title']}\n"
            f"💰 Nuevo Precio: ${deal['price']}\n"
            f"❌ Antes: ${deal['old_price']}\n"
            f"🔗 {deal['url']}"
        )
    elif source == 'coppel':
        msg = (
            f"📉 ¡BAJADA DE PRECIO EN COPPEL! ({deal['discount_pct']}% OFF)\n\n"
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
    
    import time
    
    # Simple retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Rate limiting: Sleep 1s before each request to be safe (Telegram limit is ~30 msg/sec, but safe side)
            time.sleep(1)
            
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg},
                timeout=10  # Increased timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Alerta enviada a Telegram: {deal['title'][:50]}")
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
def scan_soriana_deals():
    logger.info("=" * 60)
    logger.info("▶️ TAREA INICIADA: scan_soriana_deals")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        alerts, count = get_soriana_deals()
        
        if not alerts:
            logger.info(f"ℹ️ No se detectaron bajadas de precio significativas en Soriana ({count} productos procesados)")
            monitor.record_no_deals('soriana')
            return

        monitor.record_found_deals('soriana')
        
        logger.info(f"📊 Procesando {len(alerts)} alertas de precio de Soriana...")
        
        alerted_count = 0
        skipped_count = 0
        
        for deal in alerts:
            try:
                unique_id = deal.get('sku') or deal.get('url')
                if not unique_id:
                    continue

                cache_key = f"alerted:soriana:{unique_id}"

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
                logger.error(f"Error enviando alerta individual Soriana: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Tarea completada en {elapsed:.2f}s - {alerted_count} alertas enviadas, {skipped_count} saltadas")
        
    except Exception as e:
        logger.exception(f"❌ Error en scan_soriana_deals: {e}")
        monitor.record_failure('soriana', str(e))
    finally:
        logger.info("=" * 60)


@app.task
def scan_coppel_deals():
    """
    Dispatcher task: Reads all Coppel URLs and schedules a separate task for each.
    This prevents one long running task from blocking the worker.
    """
    logger.info("=" * 60)
    logger.info("🚀 DISPATCHER: Starting Coppel fan-out...")
    
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

    logger.info(f"📅 Scheduling {len(urls)} Coppel category tasks...")
    
    # Spawn a task for each URL
    for url in urls:
        scrape_single_coppel_category.delay(url)
        
    logger.info(f"✅ Dispatched {len(urls)} tasks.")
    logger.info("=" * 60)

@app.task
def scrape_single_coppel_category(url):
    """
    Worker task: Scrapes a SINGLE Coppel category.
    """
    task_id = scrape_single_coppel_category.request.id
    logger.info(f"▶️ [{task_id}] Processing Coppel Category: {url[-20:]}...")
    
    try:
        # Initialize service with just ONE url
        # We need to import CoppelService inside the task to avoid circular imports if any
        from app.coppel_service import CoppelService
        from app.crud import process_products
        from app.models import SessionLocal

        service = CoppelService([url]) 
        products = service.run()
        
        if products:
            logger.info(f"✅ [{task_id}] Found {len(products)} products, saving...")
            
            # Database saving logic (reused)
            db = SessionLocal()
            try:
                process_products(products, db)
                monitor.record_found_deals('coppel')
                
                # Check for alerts separately per category
                check_coppel_alerts(products, db)
                
            except Exception as e:
                logger.error(f"❌ DB Error: {e}")
            finally:
                db.close()
        else:
            logger.warning(f"⚠️ [{task_id}] No products found.")
            monitor.record_no_deals('coppel')
            
    except Exception as e:
        logger.error(f"❌ [{task_id}] Failed: {e}")
        monitor.record_failure('coppel', str(e))

def check_coppel_alerts(products, db):
    """
    Helper to send alerts for a batch of products.
    Compares scraping price vs stored DB price to find REAL drops.
    """
    from app.models import Product
    
    alerted_count = 0
    skipped_count = 0
    
    for deal in products:
        try:
            current_price = deal.get('price', 0)
            sku = deal.get('sku')
            url = deal.get('url')
            
            if current_price <= 0: continue
            
            # Find existing product in DB to compare price
            # We look for the product BEFORE the update (or we assume process_products updated it? 
            # actually process_products updates it. 
            # We need to rely on the fact that process_products updates history.
            # BUT simpler: check the PriceHistory or just check if it's significantly lower than "original_price" 
            # IF we want like other services, we usually check:
            # 1. Is new price lower than stored price? 
            # BUT process_products ALREADY updated the price in step 559.
            # So we can't easily compare "previous" price unless we fetch it before update OR check the logic intentionally.
            
            # Wait, standard pattern in this project seems to be:
            # The 'deal' dict usually comes with 'original_price' from the site, OR we check DB.
            # Let's check how officesepot does it: `update_tracked_products_officedepot` finds changes.
            
            # Since process_products ran, the DB now has the NEW price. 
            # We should probably check the PriceHistory table for the *previous* entry?
            # Or simpler: The user wants "stored price" comparison.
            
            # Let's assume we want to alert if the price ON SITE (original_price if available, or just valid discount logic)
            # Actually, most reliable "Drop" alert needs the OLD price.
            # If process_products already ran, we lost the old price in the Product table.
            
            # REVISION: To do this correctly without changing `process_products`, 
            # we should rely on `process_products` returning the "changes" or we query PriceHistory.
            
            # However, looking at the code structure provided: 
            # `scan_officedepot_deals` calls `update_tracked_products_officedepot` which does its own logic.
            
            # OPTION: We query the DB for the product. The Product table has `current_price` (which is now the NEW price).
            # We can check the `price_history` for the LAST price.
            
            # Efficient way:
            p_db = db.query(Product).filter(Product.sku == sku).first()
            if not p_db:
                # New product, maybe alert if it has a big site discount
                 orig_price = deal.get('original_price', 0)
                 if orig_price > 0 and current_price < orig_price:
                     discount = int(((orig_price - current_price) / orig_price) * 100)
                     if discount >= 40: # New product high discount
                         deal['discount_pct'] = discount
                         deal['old_price'] = orig_price
                         # Proceed to alert
                     else:
                         continue
                 else:
                     continue
            else:
                 # Product exists. 
                 # We just updated it. So PriceHistory should have an entry from "just now" and "previous".
                 # This is getting complicated to query efficiently for 1000s of products.
                 
                 # SIMPLER APPROACH requested by User "like the other services":
                 # Most services in this repo seem to filter alerts *before* DB update or return "deals" list.
                 # But here `service.run()` returns all products.
                 
                 # Let's use the 'original_price' from the SITE for now if we can't easily get history,
                 # UNLESS we change how we call `process_products`.
                 
                 # Wait, the user specifically asked: "checking discounts against the current price in the database"
                 
                 # Okay, I will implement a check against the DB *before* the huge batch update? 
                 # No, `process_products` is called at line 559. `check_coppel_alerts` at 563.
                 # The DB is already updated.
                 
                 # Correct logic: Query PriceHistory for the last 2 records.
                 from app.models import PriceHistory
                 history = db.query(PriceHistory).filter(PriceHistory.product_id == p_db.id).order_by(PriceHistory.timestamp.desc()).limit(2).all()
                 
                 if len(history) >= 2:
                     # We have history! Compare with the PREVIOUS price (history[1])
                     # history[0] is the current price we just saved
                     previous_price = history[1].price
                     current_price = float(current_price)
                     
                     if previous_price > current_price:
                         # REAL PRICE DROP DETECTED
                         drop_pct = int(((previous_price - current_price) / previous_price) * 100)
                         
                         if drop_pct >= 50:  # Alert on >50% real drops
                            deal['discount_pct'] = drop_pct
                            deal['old_price'] = previous_price
                            # Proceed to alert
                         else:
                            continue
                     else:
                         # Price same or increased
                         continue
                 else:
                     # New product (only 1 history record)
                     # User Requested: NO ALERTS for new products to avoid spam.
                     continue

            unique_id = deal.get('sku') or deal.get('url')
            if not unique_id: continue

            cache_key = f"alerted:coppel:{unique_id}"

            if not redis_client.get(cache_key):
                logger.info(f"  🔔 Alertando: {deal['name']}")
                deal['title'] = deal['name']
                # deal['old_price'] set above
                
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
