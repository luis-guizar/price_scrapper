import logging
from app.monitoring import Monitor
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_test_alert():
    logger.info("🚀 Enviando alerta de SISTEMA de prueba a Telegram...")
    monitor = Monitor()
    
    title = "Prueba de Monitor"
    message = "Esta es una alerta de prueba generada manualmente para verificar que el sistema de monitoreo puede enviar notificaciones críticas."
    
    monitor.send_system_alert(title, message)
    logger.info("✅ Intento de envío finalizado. Revisa tu Telegram.")

if __name__ == "__main__":
    send_test_alert()
