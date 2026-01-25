from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String, unique=True)
    sku = Column(String, unique=True, nullable=True)
    current_price = Column(Float)
    original_price = Column(Float, nullable=True)
    last_checked = Column(DateTime, default=datetime.utcnow)

# Conexión
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/pricedb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)