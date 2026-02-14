from sqlalchemy.orm import Session
from app.models import Product, PriceHistory
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_url(db: Session, url: str):
    return db.query(Product).filter(Product.url == url).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, 
                 search: str = None, source: str = None,
                 min_price: float = None, max_price: float = None,
                 sort_by: str = "newest", exclude: str = None):
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
    if "mercadolibre.com.mx" in url:
        product_data["source"] = "mercadolibre"
    elif "walmart.com.mx" in url:
        product_data["source"] = "walmart"
    elif "officedepot.com.mx" in url:
        product_data["source"] = "officedepot"
    elif "cyberpuerta.mx" in url:
        product_data["source"] = "cyberpuerta"
    else:
        product_data["source"] = "other"

    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Init history
    if db_product.current_price is not None:
        add_price_history(db, db_product.id, db_product.current_price)
        
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False

def add_price_history(db: Session, product_id: int, price: float):
    history = PriceHistory(product_id=product_id, price=price, timestamp=datetime.utcnow())
    db.add(history)
    db.commit()
    return history

def update_product_price(db: Session, product: Product, new_price: float):
    """
    Updates the product price and records it in history if it changed (or if forced).
    """
    old_price = product.current_price
    
    product.current_price = new_price
    product.last_checked = datetime.utcnow()
    
    # Add to history
    add_price_history(db, product.id, new_price)
    
    db.commit()
    db.refresh(product)
    return product

def get_product_history(db: Session, product_id: int):
    return db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.timestamp.asc()).all()
