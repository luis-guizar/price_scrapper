import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Product, Alert

# Connect to the exposed localhost DB
DATABASE_URL = 'postgresql://user:password@localhost:5432/pricedb'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def main():
    session = SessionLocal()
    try:
        print("Starting deletion...")
        
        # We might have cascades, but SQLAlchemy handles bulk delete without fetching objects 
        # by simply doing `DELETE FROM table ...`, which is fast. BUT `PriceHistory` backref is cascade="all, delete-orphan".
        # This relationship is on the ORM level. If we do a bulk delete like `.delete()`, the DB level foreign keys might constraint unless cascade is set on the DB side.
        # Let's see app.models.py:
        # product_id = Column(Integer, ForeignKey('products.id'))
        # If there is no ON DELETE CASCADE on the DB, a bulk delete might fail.
        # So it's safer to delete history first, or fetch and delete. Let's try bulk delete products. 
        # Actually doing a subquery delete on PriceHistory is safe.
        
        print("Deleting PriceHistory for 'coppel' products...")
        session.execute(
            text("DELETE FROM price_history WHERE product_id IN (SELECT id FROM products WHERE source = 'coppel')")
        )
        
        print("Deleting 'coppel' alerts...")
        session.execute(
            text("DELETE FROM alerts WHERE source = 'coppel' OR product_id IN (SELECT id FROM products WHERE source = 'coppel')")
        )
        
        print("Deleting 'coppel' products...")
        deleted_products = session.execute(
            text("DELETE FROM products WHERE source = 'coppel'")
        )
        
        session.commit()
        print("Successfully committed changes.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
