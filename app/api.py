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

class PaginatedResponse(BaseModel):
    data: List[ProductResponse]
    total: int
    page: int
    limit: int
    pages: int

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

@app.get("/products", response_model=PaginatedResponse)
def read_products(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, 
    source: Optional[str] = None, 
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "newest",
    exclude: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items, total = crud.get_products(
        db, skip=skip, limit=limit, search=search, source=source,
        min_price=min_price, max_price=max_price, sort_by=sort_by, exclude=exclude
    )
    
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = (total + limit - 1) // limit if limit > 0 else 0
    
    return {
        "data": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

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


# --- Smart URL Tracking ---

class TrackUrlRequest(BaseModel):
    url: str

def _detect_source(url: str) -> str:
    url_lower = url.lower()
    if "mercadolibre.com" in url_lower or "articulo.mercadolibre" in url_lower:
        return "mercadolibre"
    elif "walmart.com.mx" in url_lower:
        return "walmart"
    elif "officedepot.com.mx" in url_lower:
        return "officedepot"
    elif "cyberpuerta.mx" in url_lower:
        return "cyberpuerta"
    elif "chedraui.com.mx" in url_lower:
        return "chedraui"
    elif "elektra.com.mx" in url_lower or "elektra.mx" in url_lower:
        return "elektra"
    return "other"


@app.post("/products/preview-url")
def preview_url(req: TrackUrlRequest):
    """Scrape a URL and return product info without saving."""
    source = _detect_source(req.url)

    if source == "mercadolibre":
        from app.meli_service import MeliService
        svc = MeliService()
        item_id = svc.extract_id_from_url(req.url)
        if not item_id:
            raise HTTPException(status_code=400, detail="Could not extract MercadoLibre item ID from URL")

        original_url = req.url if req.url.startswith("http") else None
        data = svc.scrape_item(item_id, original_url=original_url)
        if not data:
            raise HTTPException(status_code=404, detail="Could not scrape product. The listing may be unavailable or rate-limited.")

        return {
            "source": source,
            "name": data["title"],
            "price": data["price"],
            "sku": data["id"],
            "url": data["permalink"],
            "thumbnail": data.get("thumbnail", ""),
            "currency": data.get("currency_id", "MXN"),
        }

    # For other sources, return basic info
    return {
        "source": source,
        "name": "",
        "price": None,
        "sku": None,
        "url": req.url,
        "thumbnail": "",
        "currency": "MXN",
    }


@app.post("/products/track-url", response_model=ProductResponse)
def track_url(req: TrackUrlRequest, db: Session = Depends(get_db)):
    """
    Smart tracking: accepts a URL, auto-detects source,
    and for supported sources (MercadoLibre), scrapes product info automatically.
    """
    source = _detect_source(req.url)

    if source == "mercadolibre":
        from app.meli_service import MeliService
        svc = MeliService()
        item_id = svc.extract_id_from_url(req.url)
        if not item_id:
            raise HTTPException(status_code=400, detail="Could not extract MercadoLibre item ID from URL")

        # Check if already tracked
        existing = db.query(Product).filter(
            Product.sku == item_id, Product.source == "mercadolibre"
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="This product is already being tracked")

        original_url = req.url if req.url.startswith("http") else None
        data = svc.scrape_item(item_id, original_url=original_url)
        if not data:
            raise HTTPException(status_code=404, detail="Could not scrape product. The listing may be unavailable or rate-limited.")

        product_data = {
            "name": data["title"],
            "url": data["permalink"],
            "sku": data["id"],
            "source": "mercadolibre",
            "current_price": data["price"],
        }
        return crud.create_product(db, product_data)

    # For other sources, create a basic entry
    existing = crud.get_product_by_url(db, url=req.url)
    if existing:
        raise HTTPException(status_code=400, detail="This product is already being tracked")

    product_data = {
        "name": "New Product",
        "url": req.url,
        "source": source,
    }
    return crud.create_product(db, product_data)
