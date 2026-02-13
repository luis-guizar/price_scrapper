import requests
from playwright.sync_api import sync_playwright
import time

URL = "https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0"

def test_requests():
    print(f"Testing requests with URL: {URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        print(f"Requests Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Requests success!")
        else:
            print("Requests failed.")
    except Exception as e:
        print(f"Requests Exception: {e}")

def test_playwright():
    print(f"Testing Playwright with URL: {URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        try:
            page.goto(URL, timeout=30000, wait_until="domcontentloaded")
            # Wait a bit
            page.wait_for_timeout(5000)
            
            content = page.content()
            print(f"Playwright Title: {page.title()}")
            
            # 1. Test Cookie Transfer
            cookies = context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}
            print(f"Playwright Cookies obtained: {len(cookie_dict)}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            }
            
            print("Testing requests with Playwright cookies...")
            try:
                resp = requests.get(URL, headers=headers, cookies=cookie_dict, timeout=20)
                print(f"Requests (w/ cookies) Status: {resp.status_code}")
            except Exception as e:
                print(f"Requests (w/ cookies) Failed: {e}")

            # 2. Check for 'impressions' in content (logic from officedepot_service.py)
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(content, 'lxml')
            scripts = soup.find_all('script')
            found_datalayer_txt = None
            
            for script in scripts:
                txt = script.get_text() or ''
                if 'dataLayer.push' in txt and 'impressions' in txt:
                    found_datalayer_txt = txt
                    break
            
            if found_datalayer_txt:
                print("✅ Found 'impressions' script in Playwright content!")
                # Try to extract one item to be sure
                match = re.search(r"'impressions'\s*:\s*\[(.*?)\]", found_datalayer_txt, re.DOTALL)
                if match:
                     print("✅ Successfully extracted impressions block via regex.")
                else:
                     print("❌ Found script but regex failed to extract impressions block.")
            else:
                print("❌ 'impressions' NOT found in Playwright content scripts.")
                # fallback check
                if 'impressions' in content:
                    print("... but 'impressions' IS in the HTML body somewhere.")

        except Exception as e:
            print(f"Playwright Exception: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_requests()
    print("-" * 20)
    test_playwright()
