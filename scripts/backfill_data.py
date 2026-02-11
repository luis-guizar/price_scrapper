import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Product
from sqlalchemy import or_

def backfill_sources():
    session = SessionLocal()
    try:
        # Find products with missing source
        products = session.query(Product).filter(or_(Product.source == None, Product.source == "")).all()
        
        print(f"Found {len(products)} products with missing source.")
        
        updated_count = 0
        for product in products:
            url = product.url.lower()
            original_source = product.source
            
            if "mercadolibre.com.mx" in url:
                product.source = "mercadolibre"
            elif "walmart.com.mx" in url:
                product.source = "walmart"
            elif "officedepot.com.mx" in url:
                product.source = "officedepot"
            elif "promodescuentos.com" in url:
                product.source = "promodescuentos"
            elif "amazon.com" in url or "amzn.to" in url:
                product.source = "amazon"
            else:
                product.source = "other"
            
            if product.source != original_source:
                updated_count += 1
                # print(f"Updated {product.name[:30]}... -> {product.source}")
        
        session.commit()
        print(f"Successfully updated {updated_count} products.")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    backfill_sources()
