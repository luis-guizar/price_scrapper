import os
import logging
from sqlalchemy import create_engine, text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener URL de la DB
# Intentamos obtenerla del entorno, sino usamos la default que usa el proyecto
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/pricedb')

def run_migration():
    logger.info(f"Conectando a la base de datos...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Usamos isolation_level="AUTOCOMMIT" para asegurar que los cambios de DDL se apliquen inmediatamente
        # y evitar problemas con bloques de transacción en algunos drivers.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            
            # 1. Agregar columna 'sku'
            logger.info("Probando agregar columna 'sku'...")
            try:
                # Nota: IF NOT EXISTS funciona en Postgres 9.6+
                connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR UNIQUE;"))
                logger.info("✅ Columna 'sku' verificada/agregada.")
            except Exception as e:
                # Si falla, puede ser que la DB sea vieja o haya otro problema.
                # A veces IF NOT EXISTS no es soportado por todas las versiones de SQL, 
                # pero Postgres lo soporta.
                logger.warning(f"⚠️ Aviso al agregar 'sku' (puede que ya exista): {e}")

            # 2. Agregar columna 'original_price'
            logger.info("Probando agregar columna 'original_price'...")
            try:
                connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS original_price FLOAT;"))
                logger.info("✅ Columna 'original_price' verificada/agregada.")
            except Exception as e:
                logger.warning(f"⚠️ Aviso al agregar 'original_price' (puede que ya exista): {e}")

            # 3. Crear tabla 'price_history'
            logger.info("Probando crear tabla 'price_history'...")
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER REFERENCES products(id),
                        price FLOAT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ Tabla 'price_history' verificada/creada.")
            except Exception as e:
                logger.error(f"❌ Error creando tabla 'price_history': {e}")
            except Exception as e:
                logger.error(f"❌ Error creando tabla 'price_history': {e}")

            # 3.5. Crear tabla 'alerts'
            logger.info("Probando crear tabla 'alerts'...")
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER,
                        price FLOAT,
                        previous_price FLOAT,
                        change_pct INTEGER,
                        source VARCHAR,
                        url VARCHAR,
                        title VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ Tabla 'alerts' verificada/creada.")
            except Exception as e:
                logger.error(f"❌ Error creando tabla 'alerts': {e}")

            # 4. Agregar columna 'source'
            logger.info("Probando agregar columna 'source'...")
            try:
                # Force commit before alter
                connection.commit()
                connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS source VARCHAR;"))
                connection.commit()
                logger.info("✅ Columna 'source' verificada/agregada CORRECTAMENTE.")
            except Exception as e:
                logger.warning(f"⚠️ Aviso al agregar 'source': {e}")
                # Sometimes it fails if transaction is aborted
                connection.rollback()

            # 5. Agregar columnas 'telegram_message_id' y 'telegram_chat_id' a 'alerts'
            # (permiten mapear una respuesta al mensaje de Telegram de vuelta a la alerta/producto)
            logger.info("Probando agregar columnas de Telegram a 'alerts'...")
            try:
                connection.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS telegram_message_id INTEGER;"))
                # BIGINT: los chat_id de supergrupos/canales de Telegram exceden un INTEGER de 32 bits
                connection.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT;"))
                logger.info("✅ Columnas 'telegram_message_id'/'telegram_chat_id' verificadas/agregadas.")
            except Exception as e:
                logger.warning(f"⚠️ Aviso al agregar columnas de Telegram: {e}")
                connection.rollback()

    except Exception as e:
        logger.error(f"❌ Error crítico conectando o migrando: {e}")
        logger.info("💡 Asegúrate de que la base de datos esté corriendo y la URL sea correcta.")

if __name__ == "__main__":
    run_migration()
