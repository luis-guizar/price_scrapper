from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.monitoring import Monitor

monitor = Monitor()

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
