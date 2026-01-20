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

@app.get("/stats")
def read_stats(db: Session = Depends(get_db)):
    try:
        product_count = db.query(Product).count()
        return {
            "status": "running.2",
            "products_count": product_count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
