from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String, unique=True)
    sku = Column(String, unique=True, nullable=True)
    source = Column(String, nullable=True)
    current_price = Column(Float)
    original_price = Column(Float, nullable=True)
    last_checked = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Relationship to history
    history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    
    product = relationship("Product", back_populates="history")

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True) # Optional link, sometimes alerts are not linked to a persisted product
    price = Column(Float)
    previous_price = Column(Float, nullable=True)
    change_pct = Column(Integer, nullable=True)
    source = Column(String)
    url = Column(String, nullable=True) # Redundant but useful if product is deleted
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    telegram_message_id = Column(Integer, nullable=True)
    telegram_chat_id = Column(BigInteger, nullable=True)


# Conexión
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/pricedb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)