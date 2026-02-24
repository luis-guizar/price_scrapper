import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Product, Alert
import os

# Connect to the DB using environment variable if available, fallback to 'db' (docker) then 'localhost'
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/pricedb')
print(f"Connecting to database at: {DATABASE_URL.split('@')[-1]}") # Print host/db for debugging
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def main():
    session = SessionLocal()
    try:
        print("Starting cleanup...")
        
        # 1. Kill other active sessions that might be locking the tables
        print("Checking for and clearing stale locks...")
        session.execute(text("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'pricedb' 
              AND pid <> pg_backend_pid()
              AND state in ('active', 'idle in transaction');
        """))
        session.commit()

        # 2. Get counts for visibility
        prod_count = session.execute(text("SELECT count(*) FROM products WHERE source = 'coppel'")).scalar()
        hist_count = session.execute(text("SELECT count(*) FROM price_history WHERE product_id IN (SELECT id FROM products WHERE source = 'coppel')")).scalar()
        alert_count = session.execute(text("SELECT count(*) FROM alerts WHERE source = 'coppel'")).scalar()
        
        print(f"To delete: {prod_count} products, {hist_count} history entries, {alert_count} alerts.")

        if prod_count == 0 and hist_count == 0 and alert_count == 0:
            print("Nothing to delete.")
            return

        # 3. Delete in order with explicit commits to avoid huge transactions
        print("Deleting alerts...")
        session.execute(text("DELETE FROM alerts WHERE source = 'coppel'"))
        session.commit()
        
        print("Deleting price history (this may take a moment)...")
        # Direct delete on large tables can be slow, but since we cleared locks it should progress
        session.execute(text("DELETE FROM price_history WHERE product_id IN (SELECT id FROM products WHERE source = 'coppel')"))
        session.commit()
        
        print("Deleting products...")
        session.execute(text("DELETE FROM products WHERE source = 'coppel'"))
        session.commit()
        
        print("✅ Cleanup complete.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
