import requests
import json

def test_search_params(query, param_type='ft'):
    base_url = "https://www.elektra.mx/api/catalog_system/pub/products/search"
    
    if param_type == 'ft':
        url = f"{base_url}?ft={query}&_from=0&_to=5"
    else:
        url = f"{base_url}?{query}&_from=0&_to=5"
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code in [200, 206]:
            products = response.json()
            print(f"Found {len(products)} products.")
            for p in products[:3]:
                print(f"- {p.get('productName')} (CatID: {p.get('categoryId')})")
        else:
            print(f"Failed with status {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)

if __name__ == "__main__":
    print("Test 1: Search for 'iphone'")
    test_search_params("iphone")
    
    print("\nTest 2: Search for 'motocicleta'")
    test_search_params("motocicleta")
    
    # Also test if we can filter by category path if we knew it, but 'ft' is easiest for the user
