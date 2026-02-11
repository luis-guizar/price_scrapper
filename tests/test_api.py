from app.models import Product, PriceHistory
from datetime import datetime

# Tests now use the client fixture from conftest.py which has the override

def test_read_products_empty(client, db):
    response = client.get("/products")
    assert response.status_code == 200
    assert response.json() == []

def test_read_products_with_data(client, db):
    # Add product
    product = Product(name="Test API", url="http://test.com", current_price=100.0, source="test")
    db.add(product)
    db.commit()
    
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test API"

def test_product_history(client, db):
    product = Product(name="History Test", url="http://hist.com", current_price=10.0)
    db.add(product)
    db.commit()
    
    history = PriceHistory(product_id=product.id, price=10.0, timestamp=datetime.utcnow())
    db.add(history)
    db.commit()
    
    response = client.get(f"/products/{product.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["price"] == 10.0
