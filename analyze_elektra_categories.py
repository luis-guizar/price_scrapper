import requests
import json
from collections import Counter

def analyze_search(query):
    url = f"https://www.elektra.mx/api/catalog_system/pub/products/search?ft={query}&_from=0&_to=19"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    print(f"\nAnalyzing '{query}'...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code in [200, 206]:
            products = response.json()
            cats = [p.get('categoryId') for p in products if p.get('categoryId')]
            
            if not cats:
                print("No categories found.")
                return

            common = Counter(cats).most_common(3)
            print(f"Top Category IDs found for '{query}':")
            for cat_id, count in common:
                # Try to get category name if possible (optional step, or just print ID)
                # Usually product has 'categories' field too with names
                cat_name = "Unknown"
                # Check first product with this cat_id
                for p in products:
                    if p.get('categoryId') == cat_id:
                        # 'categories' is usually a list of paths like ["/Technology/Telephony/"]
                        paths = p.get('categories', [])
                        if paths:
                            cat_name = paths[0]
                        break
                print(f"  - ID: {cat_id} ({count} products) -> {cat_name}")
                
            print(f"\nTo filter ONLY this category, use URL:")
            best_id = common[0][0]
            print(f"https://www.elektra.mx/api/catalog_system/pub/products/search?fq=C:{best_id}")

        else:
            print(f"Error: Status {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_search("motocicleta")
    analyze_search("iphone")
