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

    except Exception as e:
        logger.error(f"❌ Error crítico conectando o migrando: {e}")
        logger.info("💡 Asegúrate de que la base de datos esté corriendo y la URL sea correcta.")

if __name__ == "__main__":
    run_migration()
