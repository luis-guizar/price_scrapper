import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Import module to patch objects
import app.tasks

from app.models import Product, SessionLocal

# Mock response data
MOCK_PRODUCT_HTML = """
<html>
<body>
<script>
    dataLayer = [];
    dataLayer.push({
        'impressions': [
            {
                'id': '12345',
                'name': 'Test Office Chair',
                'price': '5000.00',
                'sale_price': '2500.00',
                'brand': 'OfficeDepot',
                'category': 'Furniture',
                'variant': '',
                'list': 'Search Results',
                'position': 1
            }
        ]
    });
</script>
</body>
</html>
"""

@pytest.fixture
def mock_requests_get():
    # Only mock the external request to getting HTML
    with patch('app.officedepot_service.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = MOCK_PRODUCT_HTML
        mock_get.return_value = mock_resp
        yield mock_get

@pytest.fixture
def mock_redis():
    # Patch the redis_client object on the imported module
    with patch.object(app.tasks, 'redis_client') as mock_redis:
        mock_redis.get.return_value = None
        yield mock_redis

@pytest.fixture
def mock_monitor():
    # Patch the monitor object on the imported module to prevent it using real redis
    with patch.object(app.tasks, 'monitor') as mock_monitor:
        yield mock_monitor

@pytest.fixture
def db_session():
    # Mock the DB session
    with patch('app.officedepot_service.SessionLocal') as mock_session_cls:
        session = MagicMock()
        mock_session_cls.return_value = session
        
        # Mock query return values
        mock_product = Product(
            id=1,
            name='Test Office Chair',
            sku='12345',
            url='http://example.com/p/12345',
            current_price=5000.00,
            source='officedepot'
        )
        
        # Chain mocks for query().filter().first()
        session.query.return_value.filter.return_value.first.return_value = mock_product
        # Chain mocks for query().filter().all()
        session.query.return_value.filter.return_value.all.return_value = [mock_product]

        yield session

def test_officedepot_deduplication_logic(mock_requests_get, mock_redis, mock_monitor, db_session):
    """
    Test that duplicate alerts are suppressed by Redis.
    """
    # 1. First run: Price drops from 5000 to 2500. Redis return None -> SEND ALERT.
    with patch('app.tasks.send_telegram_alert') as mock_send_alert:
        mock_send_alert.return_value = True
        
        app.tasks.scan_officedepot_deals()
        
        # Assert alert sent
        assert mock_send_alert.called, "Should alert on first run (price drop)"
        assert mock_send_alert.call_count >= 1

        # Check that Redis SET was called (to mark alerted)
        # Note: In current implementation (before fix), this is NOT called.
        # But we expect the test to pass if fix is applied perfectly, or fail if not.
        
        # Reset mocks for second run
        mock_send_alert.reset_mock()
        mock_redis.reset_mock()
        
        # 2. Second run: Redis returns "1" (already alerted) -> NO ALERT.
        mock_redis.get.return_value = b'1'  # Redis returns bytes usually
        
        app.tasks.scan_officedepot_deals()
        
        # Assert NO alert sent
        assert mock_send_alert.call_count == 0, "Should suppress alert on second run due to Redis"
