
import urllib.parse
import json
import base64

def check_url_structure():
    with open("chedraui_example_api_urls.txt", "r") as f:
        url = f.readline().strip()
        
    print(f"Analyzing URL: {url[:100]}...")
    
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    
    print("\n--- Top Level Parameters ---")
    for k, v in qs.items():
        print(f"{k}: {v[0][:50]}...")
        
    if 'variables' in qs:
        print("\n--- Variables Parameter ---")
        print(qs['variables'][0])
        
    if 'extensions' in qs:
        print("\n--- Extensions Parameter ---")
        ext_str = qs['extensions'][0]
        try:
            ext_json = json.loads(ext_str)
            print(json.dumps(ext_json, indent=2))
            
            if 'variables' in ext_json:
                print("\n--- Decoded Extensions Variables ---")
                # It seems the variables inside extensions is a base64 string
                decoded_vars = base64.b64decode(ext_json['variables']).decode('utf-8')
                print(decoded_vars)
        except Exception as e:
            print(f"Error parsing extensions: {e}")

if __name__ == "__main__":
    check_url_structure()
