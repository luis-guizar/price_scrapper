import logging
import redis
import time
from app.monitoring import Monitor

# Configurar logging para ver output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_monitor():
    logger.info("🔧 Iniciando prueba de Monitor...")
    monitor = Monitor()
    r = redis.Redis(host='redis', port=6379, db=1)
    
    service = 'test_service'
    
    # Limpiar estado previo
    r.delete(f"monitor:{service}:failures")
    r.delete(f"monitor:{service}:empty")
    
    # 1. Test Failure counting
    logger.info("  👉 Probando conteo de fallos...")
    monitor.record_failure(service, "Error de prueba 1")
    count = int(r.get(f"monitor:{service}:failures") or 0)
    logger.info(f"    Fallos actuales: {count} (Esperado: 1)")
    
    monitor.record_failure(service, "Error de prueba 2")
    count = int(r.get(f"monitor:{service}:failures") or 0)
    logger.info(f"    Fallos actuales: {count} (Esperado: 2)")
    
    # 2. Test Success reset
    logger.info("  👉 Probando reset por éxito...")
    monitor.record_success(service)
    count = r.get(f"monitor:{service}:failures")
    logger.info(f"    Fallos tras éxito: {count} (Esperado: None)")
    
    # 3. Test Empty counting
    logger.info("  👉 Probando conteo de empty...")
    monitor.record_no_deals(service)
    monitor.record_no_deals(service)
    count = int(r.get(f"monitor:{service}:empty") or 0)
    logger.info(f"    Empty count: {count} (Esperado: 2)")
    
    # 4. Test Success found deals reset
    logger.info("  👉 Probando reset por deals encontrados...")
    monitor.record_found_deals(service)
    count_e = r.get(f"monitor:{service}:empty")
    logger.info(f"    Empty count tras found deals: {count_e} (Esperado: None)")
    
    logger.info("✅ Prueba completada.")

if __name__ == "__main__":
    try:
        test_monitor()
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
