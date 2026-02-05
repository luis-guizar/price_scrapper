from sqlalchemy.orm import Session
from app.models import Product, PriceHistory
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_url(db: Session, url: str):
    return db.query(Product).filter(Product.url == url).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Product).offset(skip).limit(limit).all()

def create_product(db: Session, product_data: dict):
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
