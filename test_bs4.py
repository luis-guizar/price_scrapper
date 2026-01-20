
import requests
from bs4 import BeautifulSoup
import re
import json

URL = "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0"

def test_fetch():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Fetching {URL}...")
    response = requests.get(URL, headers=headers)
    print(f"Status: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'lxml') # using lxml as parser
    
    # Search for script
    scripts = soup.find_all('script')
    found_script = None
    for script in scripts:
        if script.string and 'dataLayer.push' in script.string and 'impressions' in script.string:
            found_script = script.string
            break
            
    if not found_script:
        print("Script with dataLayer not found via simple string check.")
        # Try finding by pattern if type is weird and string is None (sometimes bs4 puts content in .text)
        for script in scripts:
             txt = script.get_text()
             if 'dataLayer.push' in txt and 'impressions' in txt:
                 found_script = txt
                 break
    
    if found_script:
        print("✅ Found dataLayer script.")
        
        # Regex to extract impressions list: 'impressions': [ ... ]
        # The whitespace might vary.
        match = re.search(r"'impressions'\s*:\s*\[(.*?)\]", found_script, re.DOTALL)
        if match:
            impressions_str = match.group(1)
            print("Extracted impressions block length:", len(impressions_str))
            
            # Now parse the objects. They are separated by commas, inside { }.
            # Simple regex to iterate over curly braces might fail on nested, but these look flat.
            # let's try to extract each object.
            
            # This regex captures balanced braces if no nesting: \{[^{}]*\}
            item_matches = re.findall(r"\{[^{}]*\}", impressions_str)
            print(f"Found {len(item_matches)} item strings.")
            
            parsed_items = []
            for item_str in item_matches:
                # Extract fields using regex
                # 'id':'100200237'
                id_match = re.search(r"'id'\s*:\s*'([^']*)'", item_str)
                name_match = re.search(r"'name'\s*:\s*'([^']*)'", item_str)
                price_match = re.search(r"'price'\s*:\s*'([^']*)'", item_str)
                sale_price_match = re.search(r"'sale_price'\s*:\s*'([^']*)'", item_str)
                
                if id_match and name_match:
                    item = {
                        "id": id_match.group(1),
                        "name": name_match.group(1),
                        "price": price_match.group(1) if price_match else None,
                        "sale_price": sale_price_match.group(1) if sale_price_match else None
                    }
                    parsed_items.append(item)
                    print(f" - {item['name'][:40]}... (ID: {item['id']}) Price: {item['price']} Sale: {item['sale_price']}")
        else:
            print("Could not regex extract 'impressions' array.")
            print("Script start:", found_script[:200])
    
    else:
        print("Script NOT found.")

if __name__ == "__main__":
    test_fetch()
