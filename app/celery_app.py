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
    # Ejecutar cada 10 minutos (minuto 0, 10, 20, 30, 40, 50)
    'scan-keepa-every-10-mins': {
        'task': 'app.tasks.scan_amazon_deals',
        'schedule': crontab(minute='0,10,20,30,40,50'),
    },

    # Migrated to TS Backend
    # 'scan-officedepot-every-15-mins': {
    #     'task': 'app.tasks.scan_officedepot_deals',
    #     'schedule': crontab(minute='0,15,30,45'),
    # },
    # Migrated to TS Backend
    # 'scan-coppel-every-15-mins': {
    #     'task': 'app.tasks.scan_coppel_deals',
    #     'schedule': crontab(minute='7,22,37,52'),
    # },

    # --- SERVICIOS LIGEROS (API/HTML) cada 10 min ---
    'scan-cyberpuerta-every-10-mins': {
        'task': 'app.tasks.scan_cyberpuerta_deals',
        'schedule': crontab(minute='3,13,23,33,43,53'),
    },
    'scan-elektra-every-10-mins': {
        'task': 'app.tasks.scan_elektra_deals',
        'schedule': crontab(minute='6,16,26,36,46,56'),
    },
    #'scan-chedraui-every-10-mins': {
    #    'task': 'app.tasks.scan_chedraui_deals',
    #    'schedule': crontab(minute='9,19,29,39,49,59'),
    #},

    # --- TAREAS DE MANTENIMIENTO ---
    'cleanup-database-daily': {
        'task': 'app.tasks.cleanup_database_task',
        # Ejecutar todos los días a las 2:00 AM (hora de México)
        'schedule': crontab(hour=2, minute=0),
    }
}

app.conf.timezone = 'America/Mexico_City' # type: ignore

# Configuración de logging para Celery
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery configurado correctamente")