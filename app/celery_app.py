from celery import Celery
from celery.schedules import crontab
import os
import logging

# Configurar logging
from app.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')

logger.info(f"Inicializando Celery con broker: {broker_url[:30]}...")

# --- CORRECCIÓN AQUÍ ---
# Agregamos include=['app.tasks'] para que el worker lea ese archivo al arrancar
app = Celery('price_tracker', broker=broker_url, include=['app.tasks'])
# -----------------------

app.conf.beat_schedule = {
    # Ejecutar cada 5 minutos exactos (0, 5, 10, ...)
    'scan-promodescuentos-every-5-mins': {
        'task': 'app.tasks.scan_promodescuentos_deals',
        'schedule': crontab(minute='*/5'),
    },
    # Ejecutar cada 10 minutos, con offset (minuto 1, 11, 21...)
    'scan-keepa-every-10-mins': {
        'task': 'app.tasks.scan_amazon_deals',
        'schedule': crontab(minute='1,11,21,31,41,51'),
    },
    # Ejecutar cada 10 minutos, con offset (minuto 3, 13, 23...)
    'scan-walmart-every-10-mins': {
        'task': 'app.tasks.scan_walmart_deals',
        'schedule': crontab(minute='3,13,23,33,43,53'),
    },
    # Ejecutar cada 10 minutos, con offset (minuto 6, 16, 26...)
    'scan-officedepot-every-10-mins': {
        'task': 'app.tasks.scan_officedepot_deals',
        'schedule': crontab(minute='6,16,26,36,46,56'),
    },
    # Ejecutar cada 10 minutos, con offset (minuto 8, 18, 28...)
    'scan-mercadolibre-monitoring-every-10-mins': {
        'task': 'app.tasks.scan_mercadolibre_monitoring',
        'schedule': crontab(minute='8,18,28,38,48,58'),
    },
    # Ejecutar diariamente a las 4:00 AM UTC
    'scan-mercadolibre-discovery-daily': {
        'task': 'app.tasks.scan_mercadolibre_discovery',
        'schedule': crontab(hour=4, minute=0),
        'args': (["laptop gamer", "rtx 4060", "silla ergonómica", "monitor 144hz", "smart tv", "iPhone", "logitech", "macbook", "Samsung Galaxy"], 'relevancia', True)
    },
}

app.conf.timezone = 'UTC' # type: ignore

# Configuración de logging para Celery
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery configurado correctamente")