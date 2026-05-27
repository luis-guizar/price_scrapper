from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Product, PriceHistory, Alert
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_url(db: Session, url: str):
    return db.query(Product).filter(Product.url == url).first()

def get_products(db: Session, skip: int = 0, limit: int = 100,
                 search: str = None, source: str = None,
                 min_price: float = None, max_price: float = None,
                 sort_by: str = "newest", exclude: str = None,
                 min_history_count: int = None):
    query = db.query(Product)
    
    # Filters
    if source:
        query = query.filter(Product.source == source)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter((Product.name.ilike(search_term)) | (Product.sku.ilike(search_term)))
        
    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)
        
    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)
        
    if exclude:
        exclude_terms = exclude.split()
        for term in exclude_terms:
            term_clean = f"%{term}%"
            query = query.filter(~Product.name.ilike(term_clean))

    if min_history_count is not None:
        history_count = (
            db.query(func.count(PriceHistory.id))
            .filter(PriceHistory.product_id == Product.id)
            .scalar_subquery()
        )
        query = query.filter(history_count >= min_history_count)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.current_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.current_price.desc())
    else: # default newest
        query = query.order_by(Product.id.desc())
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return items, total

def create_product(db: Session, product_data: dict):
    # Auto-detect source
    url = product_data.get("url", "")
    if "officedepot.com.mx" in url:
        product_data["source"] = "officedepot"
    elif "cyberpuerta.mx" in url:
        product_data["source"] = "cyberpuerta"
    elif "chedraui.com.mx" in url:
        product_data["source"] = "chedraui"
    elif "elektra.com.mx" in url:
        product_data["source"] = "elektra"
    elif "coppel.com" in url:
        product_data["source"] = "coppel"
    else:
        # Only set to 'other' if source isn't already provided
        if "source" not in product_data:
            product_data["source"] = "other"

    # Set original_price as anchor if not explicitly provided
    if 'original_price' not in product_data or not product_data['original_price']:
        product_data['original_price'] = product_data.get('current_price')

    # Filter keys to match Product model
    valid_keys = ['name', 'url', 'sku', 'source', 'current_price', 'original_price', 'last_checked', 'is_active']
    filtered_data = {k: v for k, v in product_data.items() if k in valid_keys}

    db_product = Product(**filtered_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Init history automatically handled by DB trigger
    # if db_product.current_price is not None:
    #     add_price_history(db, db_product.id, db_product.current_price)
        
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False

def add_price_history(db: Session, product_id: int, price: float):
    history = PriceHistory(product_id=product_id, price=price, timestamp=datetime.now())
    db.add(history)
    db.commit()
    return history

def update_product_price(db: Session, product: Product, new_price: float):
    """
    Updates the product price and records it in history if it changed (or if forced).
    """
    product.current_price = new_price
    product.last_checked = datetime.now()
    
    # Add to history (Now handled by DB trigger)
    # add_price_history(db, product.id, new_price)
    
    db.commit()
    db.refresh(product)
    return product

def get_product_history(db: Session, product_id: int):
    return db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.timestamp.asc()).all()

def process_products(products: list, db: Session):
    """
    Process a list of products: create or update them in the database.
    Does not return alerts, just processes storage.
    """
    count = 0
    for p_data in products:
        try:
            sku = p_data.get('sku')
            url = p_data.get('url')
            source = p_data.get('source')
            price = p_data.get('price')
            
            # Map 'price' to 'current_price' 
            if 'current_price' not in p_data and price is not None:
                p_data['current_price'] = price
                
            # Try to find existing product
            product = None
            if sku and source:
                product = db.query(Product).filter(Product.sku == sku, Product.source == source).first()
            
            if not product and url:
                product = db.query(Product).filter(Product.url == url).first()
                
            if product:
                # Update
                new_price = p_data.get('current_price')
                if new_price is not None:
                    # Check for price change
                    if abs(product.current_price - new_price) > 0.1:
                        update_product_price(db, product, new_price)
                        
                # Update other fields
                product.last_checked = datetime.now()
                # NEVER overwrite original_price — it's our historical anchor
                # Only set it if it was previously NULL (backfill)
                if not product.original_price and product.current_price:
                    product.original_price = product.current_price
                
                # Check if we should update name or sku if it was missing?
                if not product.sku and sku:
                    product.sku = sku

                db.commit()

            else:
                # Create using create_product (will auto-set original_price)
                create_product(db, p_data)
            
            count += 1
        except Exception as e:
            logger.error(f"Error processing product {p_data.get('sku', 'unknown')}: {e}")
            db.rollback()
            continue
            
    return count

def create_alert(db: Session, alert_data: dict):
    # Filter valid keys
    valid_keys = ['product_id', 'price', 'previous_price', 'change_pct', 'source', 'url', 'title', 'created_at']
    filtered_data = {k: v for k, v in alert_data.items() if k in valid_keys}
    
    db_alert = Alert(**filtered_data)
    db.add(db_alert)
    db.commit()
    return db_alert

def get_alerts(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

def get_alerts_count(db: Session):
    return db.query(Alert).count()

def prune_database(db: Session, days: int = 30):
    """
    Deletes products (and their history) that haven't been updated in `days` days,
    and alerts older than `days` days.
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Prune old alerts
    alerts_deleted = db.query(Alert).filter(Alert.created_at < cutoff_date).delete(synchronize_session=False)
    
    # Prune old products
    # Due to cascade="all, delete-orphan", this should also delete related PriceHistory in SQLAlchemy
    # if queried and deleted object by object, OR handled by DB foreign keys on delete cascade.
    # We will do a bulk delete, but let's make sure PriceHistory is deleted first or rely on DB.
    # Since we set up Prisma without explicit cascading, it's safer to delete PriceHistory first 
    # for the old products, then delete the products.
    
    old_products_query = db.query(Product).filter(Product.last_checked < cutoff_date)
    # Get IDs of products to delete
    old_product_ids = [p.id for p in old_products_query.all()]
    
    if old_product_ids:
        # Delete history belonging to those products
        db.query(PriceHistory).filter(PriceHistory.product_id.in_(old_product_ids)).delete(synchronize_session=False)
        
    products_deleted = old_products_query.delete(synchronize_session=False)
    
    db.commit()
    
    return {
        "deleted_products": products_deleted,
        "deleted_alerts": alerts_deleted
    }

