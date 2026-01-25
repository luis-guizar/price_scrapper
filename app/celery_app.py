from celery import Celery
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
    'scan-keepa-every-10-mins': {
        'task': 'app.tasks.scan_amazon_deals',
        'schedule': 600,  # 10 minutos
    },
    'scan-promodescuentos-every-10-mins': {
        'task': 'app.tasks.scan_promodescuentos_deals',
        'schedule': 60,  # 1 minuto
    },
    'scan-officedepot-every-10-mins': {
        'task': 'app.tasks.scan_officedepot_deals',
        'schedule': 300,
    },
    'scan-walmart-every-30-mins': {
        'task': 'app.tasks.scan_walmart_deals',
        'schedule': 1800,  # 30 minutos
    },
    'scan-mercadolibre-monitoring-every-30-mins': {
        'task': 'app.tasks.scan_mercadolibre_monitoring',
        'schedule': 1800,  # 30 minutos
    },
    'scan-mercadolibre-discovery-daily': {
        'task': 'app.tasks.scan_mercadolibre_discovery',
        'schedule': 86400,  # 24 horas (diario)
        'args': (["laptop gamer", "rtx 4060", "silla ergonómica", "monitor 144hz","smart tv", "iPhone","logitech", "macbook", "Samsung Galaxy"], 'relevancia', True)
    },
}

app.conf.timezone = 'UTC' # type: ignore

# Configuración de logging para Celery
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery configurado correctamente")