import requests
import xml.etree.ElementTree as ET
import re

def get_categories():
    sitemap_url = "https://www.soriana.com/sitemap_11-category.xml"
    try:
        response = requests.get(sitemap_url, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        categories = []
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url in root.findall('s:url', ns):
            loc = url.find('s:loc', ns).text
            # Extract the last part of the URL as a potential cgid
            match = re.search(r'/([^/]+)/$', loc)
            if match:
                cgid = match.group(1)
                categories.append(cgid)
        return sorted(list(set(categories)))
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def main():
    cgids = get_categories()
    if not cgids:
        # Fallback to a core set if sitemap fails
        cgids = ["pantallas", "laptops", "celulares", "desbloqueados", "consolas", "videojuegos", "linea-blanca", "electrodomesticos", "juguetes", "motos", "muebles", "colchones", "tablets", "audio", "smartwatch"]
    
    # Priority keywords for price tracking
    priority_keywords = [
        'pantallas', 'laptops', 'celulares', 'desbloqueados', 'consolas', 
        'videojuegos', 'linea-blanca', 'electrodomesticos', 'juguetes', 
        'motos', 'muebles', 'colchones', 'tablets', 'audio', 'smartwatch',
        'computo', 'monitores', 'gadgets', 'relojes', 'camaras', 'audio-y-video'
    ]
    
    # Filter to get a more manageable but useful list
    relevant_cgids = [c for c in cgids if any(k in c.lower() for k in priority_keywords)]
    
    # Avoid too many very specific sub-categories if possible, or just keep them all if under 100
    # For now, let's keep it to a high-quality 50-60
    final_cgids = sorted(list(set(relevant_cgids)))[:80] # Limit to 80 for performance
    
    base_url = "https://www.soriana.com/on/demandware.store/Sites-Soriana-Site/default/Search-UpdateGrid?cgid={}&sz=100"
    urls = [base_url.format(cgid) for cgid in final_cgids]
    
    output_file = "soriana_urls.txt"
    with open(output_file, "w") as f:
        for url in urls:
            f.write(url + "\n")
            
    print(f"Successfully inferred and updated {len(urls)} URLs in {output_file}")

if __name__ == "__main__":
    main()
