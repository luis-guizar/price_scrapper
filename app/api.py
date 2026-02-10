import requests
import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product, PriceHistory
from app import crud
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelegramNotification(BaseModel):
    message: str

@app.post("/notifications/telegram")
def send_telegram_notification(notification: TelegramNotification):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        raise HTTPException(status_code=500, detail="Telegram credentials not configured")
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    formatted_message = f"📢 ACTUALIZACIÓN MANUAL\n\n{notification.message}"
    
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": formatted_message}, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Telegram API Error: {response.text}")
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.monitoring import Monitor
monitor = Monitor()

# --- Pydantic Models ---
class ProductBase(BaseModel):
    name: str
    url: str
    sku: Optional[str] = None
    source: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    last_checked: Optional[datetime]

    class Config:
        orm_mode = True

class PriceHistoryResponse(BaseModel):
    id: int
    price: float
    timestamp: datetime

    class Config:
        orm_mode = True

# --- Endpoints ---

@app.get("/stats")
def read_stats(db: Session = Depends(get_db)):
    try:
        product_count = db.query(Product).count()
        services_status = monitor.get_services_status()
        
        return {
            "status": "running",
            "products_count": product_count,
            "services": services_status
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/products", response_model=List[ProductResponse])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_url(db, url=product.url)
    if db_product:
        raise HTTPException(status_code=400, detail="Product already registered")
    return crud.create_product(db, product.dict())

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    success = crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}

@app.get("/products/{product_id}/history", response_model=List[PriceHistoryResponse])
def read_product_history(product_id: int, db: Session = Depends(get_db)):
    history = crud.get_product_history(db, product_id)
    return history

