import logging
import logging.handlers
import os
from datetime import datetime

# Crear directorio de logs si no existe
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Formato detallado de logs
DETAILED_FORMAT = '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s'
SIMPLE_FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'

def setup_logging(level=logging.INFO):
    """
    Configura el logging para toda la aplicación
    
    - Console: INFO y superiores
    - File: DEBUG y superiores (historial completo)
    - File (errors): ERROR y superiores
    """
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Limpiar handlers existentes
    root_logger.handlers = []
    
    # ============== HANDLER 1: CONSOLE (INFO) ==============
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # ============== HANDLER 2: FILE DEBUG (historial) ==============
    log_file = os.path.join(LOG_DIR, 'price_tracker.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB por archivo
        backupCount=5,  # Mantener 5 archivos históricos
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # ============== HANDLER 3: FILE ERRORS ==============
    error_file = os.path.join(LOG_DIR, 'errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    return root_logger

# Configurar logging al importar este módulo
setup_logging()
logger = logging.getLogger(__name__)
logger.info("Logging configurado correctamente")
