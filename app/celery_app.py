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
}

app.conf.timezone = 'UTC' # type: ignore

# Configuración de logging para Celery
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery configurado correctamente")