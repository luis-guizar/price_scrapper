"""
Backfill original_price for all existing products.

For each product where original_price is NULL:
  - Set original_price = the FIRST price ever recorded in price_history
  - If no history exists, use current_price

This ensures the anchor is the real historical first price, not just today's price.

Usage:
  docker exec worker python -m scripts.backfill_original_price
  OR
  python scripts/backfill_original_price.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Product, PriceHistory
from sqlalchemy import func

def backfill():
    db = SessionLocal()
    try:
        # Find all products with NULL original_price
        products = db.query(Product).filter(Product.original_price == None).all()
        print(f"Found {len(products)} products with NULL original_price")
        
        updated = 0
        for p in products:
            # Get the FIRST (oldest) price from history
            first_history = db.query(PriceHistory).filter(
                PriceHistory.product_id == p.id
            ).order_by(PriceHistory.timestamp.asc()).first()
            
            if first_history:
                p.original_price = first_history.price
            else:
                # No history at all, use current_price
                p.original_price = p.current_price
            
            updated += 1
            
            # Commit in batches of 500
            if updated % 500 == 0:
                db.commit()
                print(f"  ...updated {updated}/{len(products)}")
        
        db.commit()
        print(f"✅ Done. Updated {updated} products.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
