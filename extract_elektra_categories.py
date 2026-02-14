import requests
import json

def get_categories():
    url = "https://www.elektra.mx/api/catalog_system/pub/category/tree/3"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            categories = response.json()
            
            flat_list = []
            
            def flatten(cats, path=""):
                for cat in cats:
                    current_path = f"{path}/{cat['name']}"
                    flat_list.append({
                        "id": cat["id"],
                        "name": cat["name"],
                        "path": current_path,
                        "url": cat["url"]
                    })
                    if cat.get("children"):
                        flatten(cat["children"], current_path)
            
            flatten(categories)
            
            # Sort by path
            flat_list.sort(key=lambda x: x['path'])
            
            with open("elektra_categories_db.txt", "w", encoding="utf-8") as f:
                f.write(f"{'ID':<10} | {'PATH'}\n")
                f.write("-" * 60 + "\n")
                for item in flat_list:
                    f.write(f"{item['id']:<10} | {item['path']}\n")
            
            print(f"Successfully saved {len(flat_list)} categories to elektra_categories_db.txt")
        else:
            print(f"Failed to fetch categories. Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_categories()
