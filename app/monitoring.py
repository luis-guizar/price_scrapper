import os
import logging
import requests
import redis
from datetime import datetime
import urllib3.util.connection as _urllib3_cn
_urllib3_cn.HAS_IPV6 = False  # prefer IPv4; prevents ENETUNREACHABLE if IPv6 is disabled in container

# Configurar logging
logger = logging.getLogger(__name__)

# Configuración de Redis
# Usamos el db 1, el mismo que en tasks.py para las alertas de productos, 
# pero idealmente podríamos usar otro db si quisiéramos separar lógica.
redis_client = redis.Redis(host='redis', port=6379, db=1)

class Monitor:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_ALERTS_CHAT_ID')
        
        # Umbrales
        self.THRESHOLDS = {
            'keepa': {
                'failures': 3,     # 3 fallos seguidos (excepciones)
                'empty': 20        # 20 veces seguidas encontrando 0 productos (~4 horas si es cada 12 min)
            },
            'promodescuentos': {
                'failures': 3,
                'empty': 10        # ~1h 40m si es cada 10 min
            },
            'officedepot': {
                'failures': 3,
                'empty': 50        # Es normal que no encuentre bajadas de precio seguido
            }
        }
    
    def _get_key(self, service_name, type_):
        """Genera la clave de Redis: monitor:keepa:failures"""
        return f"monitor:{service_name}:{type_}"

    def send_system_alert(self, title, message):
        """Envía una alerta de SISTEMA a Telegram"""
        if not self.telegram_token or not self.chat_id:
            logger.error("❌ No se puede enviar alerta de sistema: faltan credenciales")
            return

        full_msg = (
            f"⚠️ **SYSTEM ALERT** ⚠️\n\n"
            f"**{title}**\n"
            f"{message}\n\n"
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                json={"chat_id": self.chat_id, "text": full_msg, "parse_mode": "Markdown"},
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"✅ Alerta de sistema enviada: {title}")
            else:
                logger.error(f"❌ Error enviando alerta sistema: {response.text}")
        except Exception as e:
            logger.error(f"❌ Excepción enviando alerta sistema: {e}")

    def record_success(self, service_name):
        """Resetea los contadores de fallo tras un éxito"""
        f_key = self._get_key(service_name, 'failures')
        e_key = self._get_key(service_name, 'empty')
        
        # Si había fallos previos, logueamos que se recuperó
        failures = int(redis_client.get(f_key) or 0)
        if failures > 0:
            logger.info(f"✅ {service_name} se ha recuperado tras {failures} fallos.")
            # Opcional: Enviar alerta de recuperación si estaba en estado crítico
            
        redis_client.delete(f_key)
        redis_client.delete(e_key)

    def record_failure(self, service_name, error_msg):
        """Registra un fallo (excepción)"""
        key = self._get_key(service_name, 'failures')
        count = redis_client.incr(key)
        
        limit = self.THRESHOLDS.get(service_name, {}).get('failures', 3)
        
        logger.warning(f"⚠️ {service_name} fallo #{count}/{limit}: {error_msg}")
        
        if count == limit:
            self.send_system_alert(
                f"Fallas repetidas en {service_name}",
                f"El servicio ha fallado {count} veces consecutivas.\nError reciente: `{error_msg}`"
            )
        elif count > limit and count % 10 == 0:
            # Recordatorio cada 10 fallos extra
             self.send_system_alert(
                f"Persisten fallas en {service_name}",
                f"El servicio lleva {count} fallos consecutivos.\nRevisar logs urgente."
            )

    def record_empty(self, service_name):
        """Registra que el servicio corrió bien pero no halló productos (posible error lógico/layout)"""
        key = self._get_key(service_name, 'empty')
        # No reseteamos failures aquí, porque run exitoso = 0 failures.
        # Pero reseteamos failures explícitamente en record_success/record_empty?
        # Sí, un empty result implica que NO hubo crash.
        self.record_success(service_name) # Resetea failures, pero "empty" es un track separado
        
        # Re-incrementamos empty porque record_success lo borró (o no debería borrarlo?)
        # Ajuste: record_success debería borrar failures. 
        # Pero si es empty, ¿es success? Técnicamente sí (no crash).
        # Vamos a separar:
        #   record_success_found_deals -> borra failures Y empty
        #   record_success_no_deals -> borra failures, incrementa empty
        
        # Corrección lógica Monitor:
        # record_success -> Se encontraron deals. Todo OK. Borra todo.
        pass

    def record_found_deals(self, service_name):
        """Se ejecutó correctamente Y encontró deals"""
        f_key = self._get_key(service_name, 'failures')
        e_key = self._get_key(service_name, 'empty')
        redis_client.delete(f_key)
        redis_client.delete(e_key)

    def record_no_deals(self, service_name):
        """Se ejecutó correctamente PERO NO encontró deals"""
        f_key = self._get_key(service_name, 'failures')
        redis_client.delete(f_key) # No hubo crash
        
        e_key = self._get_key(service_name, 'empty')
        count = redis_client.incr(e_key)
        
        limit = self.THRESHOLDS.get(service_name, {}).get('empty', 20)
        
        if count == limit:
            self.send_system_alert(
                f"Sin resultados en {service_name}",
                f"El servicio lleva {count} ejecuciones sin encontrar NADA.\nPosible cambio de layout, bloqueo o IP baneada."
            )

    def get_services_status(self):
        """Devuelve el estado actual de los servicios monitoreados"""
        status = {}
        for service in self.THRESHOLDS.keys():
            f_key = self._get_key(service, 'failures')
            e_key = self._get_key(service, 'empty')
            
            failures = int(redis_client.get(f_key) or 0)
            empty = int(redis_client.get(e_key) or 0)
            
            status[service] = {
                "failures": failures,
                "consecutive_empty": empty,
                "status": "ok" if failures == 0 and empty < self.THRESHOLDS[service]['empty'] else "warning"
            }
            # Si supera umbral, poner status 'critical'
            if failures >= self.THRESHOLDS[service]['failures'] or empty >= self.THRESHOLDS[service]['empty']:
                status[service]['status'] = 'critical'
                
        return status
