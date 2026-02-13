from app.officedepot_service import get_officedepot_deals, update_tracked_products_officedepot, fetch_officedepot_products
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_service_integration():
    print("--- Testing Service Integration ---")
    
    # 1. Test update_tracked_products_officedepot (Should be disabled)
    print("\n1. Testing update_tracked_products (Expected: Disabled/Empty)")
    results = update_tracked_products_officedepot()
    print(f"Result: {results}")
    assert results == [], "Detailed update should be disabled and return empty list"
    
    # 2. Test fetch_officedepot_products directly
    print("\n2. Testing fetch_officedepot_products (single URL)")
    url = "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0"
    products = fetch_officedepot_products(url)
    print(f"Products found: {len(products)}")
    
    if len(products) > 0:
        print(f"Sample product: {products[0]}")
        assert "@type" in products[0]
        assert "name" in products[0]
        assert "offers" in products[0]
    else:
        print("⚠️ No products found. This might be due to empty category or parsing issue.")

    print("\n✅ Verification Complete")

if __name__ == "__main__":
    test_service_integration()
