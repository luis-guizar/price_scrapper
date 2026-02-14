import requests
import json

def test_elektra():
    # Base search with pagination
    url = "https://www.elektra.mx/api/catalog_system/pub/products/search?_from=0&_to=5"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Generic Search Status: {response.status_code}")
        
        if response.status_code in [200, 206]:
            products = response.json()
            if products:
                first_product = products[0]
                print(f"Product Name: {first_product.get('productName')}")
                print(f"Product ID: {first_product.get('productId')}")
                print(f"Category ID: {first_product.get('categoryId')}")
                
                # Check for SKUs
                if 'items' in first_product:
                    print(f"Number of SKUs: {len(first_product['items'])}")
                    for item in first_product['items']:
                        print(f"- SKU ID: {item.get('itemId')}")
                        print(f"- Name: {item.get('name')}")
                        print(f"- Sellers: {len(item.get('sellers', []))}")
                else:
                    print("No 'items' key found (SKUs usually live here)")
                
                # Test Category Search
                cat_id = first_product.get('categoryId')
                if cat_id:
                    print(f"\nTesting Category Search for ID: {cat_id}")
                    cat_url = f"https://www.elektra.mx/api/catalog_system/pub/products/search?fq=C:{cat_id}"
                    cat_response = requests.get(cat_url, headers=headers)
                    print(f"Category Search Status: {cat_response.status_code}")
                    if cat_response.status_code == 200:
                        print(f"Category Search Results: {len(cat_response.json())}")
                    else:
                        print("Category search failed")
            else:
                print("No products returned")
        else:
            print("Response content:", response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_elektra()
