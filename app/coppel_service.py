import logging
import json
import time
import re
import urllib.parse
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product, PriceHistory
from playwright.async_api import async_playwright

# Configurar logging
logger = logging.getLogger(__name__)

class CoppelService:
    def __init__(self, urls):
        self.urls = urls
        # Coppel specific headers not needed for Playwright generally, 
        # but user agent is set in launch options.

    def _extract_id_from_url(self, url):
        """
        Extract categoryId from URL.
        Supports:
        - GraphQL URLs (variables={"categoryId":"cat123"})
        - Standard URLs (.../cat000101)
        """
        try:
            # 1. Try GraphQL variables
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            variables_str = params.get('variables', [''])[0]
            if variables_str:
                variables = json.loads(variables_str)
                if variables.get('categoryId'):
                    return variables.get('categoryId')
            
            # 2. Try Regex for catID in path (e.g. /cat000123)
            match = re.search(r'/(cat\d+)', url)
            if match:
                return match.group(1)
                
        except Exception as e:
            logger.error(f"Error extracting ID from URL {url[:50]}: {e}")
        return None

    def _extract_products_from_page(self, page):
        """Extract products from window.__NEXT_DATA__."""
        # This method was synchronous and relied on page.evaluate
        # But we are moving to async, so this helper is less useful directly on the page object 
        # unless passed in. Instead, we extract JSON data and use _extract_json_products
        pass

    def run(self):
        """Sync wrapper for async execution"""
        return asyncio.run(self.run_async())

    async def run_async(self):
        logger.info("Starting optimized Coppel scrape (Async Parallel)...")
        all_products = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            # Helper to process a single URL in a new page
            async def process_page_url(target_url):
                page = await context.new_page()
                try:
                    # Block heavy resources for speed
                    await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
                    
                    await page.goto(target_url, timeout=40000, wait_until="domcontentloaded")
                    next_data = await page.evaluate("() => window.__NEXT_DATA__")
                    if next_data:
                        return self._extract_json_products(next_data)
                except Exception as e:
                    logger.warning(f"Failed to scrape {target_url}: {e}")
                finally:
                    await page.close()
                return []

            for url in self.urls:
                try:
                    category_id = self._extract_id_from_url(url)
                    if not category_id: continue
                        
                    base_url = f"https://www.coppel.com/ct/{category_id}"
                    logger.info(f"Scanning category: {category_id}...")
                    
                    main_page = await context.new_page()
                    try:
                        # 1. Get initial page & total count
                        await main_page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
                        await main_page.goto(base_url, timeout=60000, wait_until="domcontentloaded")
                        next_data = await main_page.evaluate("() => window.__NEXT_DATA__")
                        
                        if not next_data:
                            logger.warning("No data found on main page.")
                            continue
                            
                        first_batch = self._extract_json_products(next_data)
                        all_products.extend(first_batch)
                        
                        page_props = next_data.get('props', {}).get('pageProps', {})
                        total_count = page_props.get('PLPProducts', {}).get('totalCount', 0)
                        
                        logger.info(f"  Found {total_count} products. Processing remaining pages in parallel...")
                        
                        if total_count > 24:
                            page_size = 24
                            max_pages = min((total_count // page_size) + 1, 15)
                            
                            # Prepare list of all pagination URLs needed
                            pagination_urls = []
                            for p_num in range(2, max_pages + 1):
                                begin_index = (p_num - 1) * page_size
                                pagination_urls.append(f"{base_url}?beginIndex={begin_index}")
                            
                            # Process in batches of N parallel tasks
                            batch_size = 5
                            for i in range(0, len(pagination_urls), batch_size):
                                chunk = pagination_urls[i:i + batch_size]
                                logger.info(f"    Fetching batch {i//batch_size + 1} ({len(chunk)} pages)...")
                                
                                tasks = [process_page_url(u) for u in chunk]
                                results = await asyncio.gather(*tasks)
                                
                                for res in results:
                                    if res:
                                        all_products.extend(res)
                                
                                # Small delay between batches to be nice
                                await asyncio.sleep(0.5)

                    except Exception as e:
                        logger.error(f"Error processing {base_url}: {e}")
                    finally:
                        await main_page.close()

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
            
            await browser.close()
            
        return all_products

    def _parse_api_product(self, p):
        """Parse product from direct API JSON (slightly different structure usually)."""
        try:
            name = p.get('name')
            sku = p.get('sku')
            href = p.get('href') or p.get('url')
            
            if not name or not sku: return None
            
            url = f"https://www.coppel.com{href}" if href and not href.startswith('http') else href
            
            # Price in API is usually simpler
            price = 0.0
            original_price = 0.0
            
            price_obj = p.get('price', {})
            # API often returns: { "discountedPrice": "1299.0", "salesPrice": "1599.0" }
            
            def parse_val(v):
                if not v: return 0.0
                if isinstance(v, str): return float(v.replace(',',''))
                return float(v)
            
            d_price = parse_val(price_obj.get('discountedPrice'))
            s_price = parse_val(price_obj.get('salesPrice'))
            
            if d_price > 0:
                price = d_price
                original_price = s_price
            else:
                price = s_price
                
            image = p.get('thumbnail') or p.get('image')
            
            return {
                "name": name,
                "sku": sku,
                "url": url,
                "price": price,
                "original_price": original_price,
                "image": image,
                "source": "coppel"
            }
        except:
            return None

    def _extract_json_products(self, next_data):
        """Helper to extract products from a __NEXT_DATA__ dict."""
        extracted = []
        try:
            page_props = next_data.get('props', {}).get('pageProps', {})
            
            products_list = []
            
            # Try PLPProducts (Dictionary with 'products' list)
            plp_products = page_props.get('PLPProducts', {})
            if isinstance(plp_products, dict):
                 products_list = plp_products.get('products', [])
            
            # If not found, try apolloState for other page types
            if not products_list:
                apollo_state = page_props.get('apolloState') or next_data.get('props', {}).get('apolloState') or page_props.get('appData', {}).get('apolloState')
                if apollo_state:
                    for key, val in apollo_state.items():
                        if key.startswith("LucidProduct:") and isinstance(val, dict):
                            products_list.append(val)

            for p in products_list:
                # Same parsing logic as _extract_products_from_page
                item = self._parse_single_product(p)
                if item:
                    extracted.append(item)
        except Exception as e:
             logger.warning(f"Error parsing JSON products: {e}")
        return extracted

    def _parse_single_product(self, p):
        """Standardized parser for a product dictionary."""
        try:
            name = p.get('name')
            sku = p.get('sku') or p.get('partNumber')
            url_slug = p.get('url') or p.get('seo_token') or p.get('href')
            if not url_slug or not name: return None

            if not url_slug.startswith('http'):
                product_url = f"https://www.coppel.com{ '/' if not url_slug.startswith('/') else ''}{url_slug}"
            else:
                product_url = url_slug

            def parse_price(val):
                if isinstance(val, (int, float)): return float(val)
                if isinstance(val, str):
                    val = val.replace(',', '').replace('$', '').strip()
                    return float(val) if val else 0.0
                return 0.0

            # Extract price logic
            price_info = p.get('price', {})
            p_sales = parse_price(price_info.get('salesPrice') or price_info.get('formattedPriceValue'))
            p_list = parse_price(price_info.get('listPrice') or price_info.get('formattedListPrice'))
            p_disc = parse_price(price_info.get('discountedPrice'))
            
            candidates = [x for x in [p_disc, p_sales, p_list] if x > 0]
            if not candidates: return None
            
            current_price = min(candidates)
            original_price = max(candidates) if len(candidates) > 1 else 0.0

            image = p.get('thumbnail') or p.get('fullImage')
            if isinstance(image, list) and image: image = image[0]

            return {
                "name": name,
                "sku": sku,
                "url": product_url,
                "price": current_price,
                "original_price": original_price,
                "image": image,
                "source": "coppel"
            }
        except:
            return None


