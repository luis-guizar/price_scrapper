import pytest
from unittest.mock import MagicMock, patch
from app.mercadolibre_service import search_products
from app.walmart_service import process_products as process_walmart
from app.officedepot_service import process_products as process_officedepot

# --- Mercado Libre Tests ---
def test_ml_search_products_creates_correct_source(db):
    # Patch SessionLocal in the service module to return our test db
    with patch('app.mercadolibre_service.SessionLocal') as mock_session_cls:
        mock_session_cls.return_value = db
        
        # Mock requests to return HTML with one product
        with patch('app.mercadolibre_service.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '''
            <html>
                <li class="ui-search-layout__item">
                    <a href="https://articulo.mercadolibre.com.mx/MLM-123-test" class="ui-search-link">Link</a>
                    <h2 class="ui-search-item__title">Test Product</h2>
                    <div class="ui-search-price__second-line">
                        <span class="andes-money-amount__fraction">1000</span>
                    </div>
                </li>
            </html>
            '''
            mock_get.return_value = mock_response

            # Call function
            products = search_products(["test"], sort_by='relevancia')
        
    # Verify in DB
    from app.models import Product
    db_product = db.query(Product).filter(Product.name == "Test Product").first()
    assert db_product is not None
    assert db_product.source == "mercadolibre"
    assert db_product.current_price == 1000.0

# --- Walmart Tests ---
def test_walmart_process_products_creates_correct_source(db):
    products_data = [{
        "name": "Walmart TV",
        "url": "https://www.walmart.com.mx/tv",
        "sku": "12345",
        "offers": {"price": 5000}
    }]
    
    with patch('app.walmart_service.SessionLocal') as mock_session_cls:
        mock_session_cls.return_value = db
        
        # Process
        process_walmart(products_data)
    
    # Verify
    from app.models import Product
    db_product = db.query(Product).filter(Product.name == "Walmart TV").first()
    assert db_product is not None
    assert db_product.source == "walmart"

# --- Office Depot Tests ---
def test_officedepot_process_products_creates_correct_source(db):
    products_data = [{
        "name": "Desk Chair",
        "url": "https://www.officedepot.com.mx/chair",
        "sku": "OD-123",
        "offers": {"price": 1500}
    }]
    
    with patch('app.officedepot_service.SessionLocal') as mock_session_cls:
        mock_session_cls.return_value = db
        
        process_officedepot(products_data)
    
    from app.models import Product
    db_product = db.query(Product).filter(Product.name == "Desk Chair").first()
    assert db_product is not None
    assert db_product.source == "officedepot"
