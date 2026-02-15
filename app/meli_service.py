import requests
import random
import re
import json
import time
import logging
from datetime import datetime
from app.models import SessionLocal, Product, PriceHistory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MeliService — Web Scraping approach (public HTML + JSON-LD)
# ---------------------------------------------------------------------------

# Pool of realistic User-Agent strings (Chrome, Firefox, Edge on Win/Mac/Linux)
_USER_AGENTS = [
    # Chrome — Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    # Chrome — Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome — Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox — Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Firefox — Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Firefox — Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Edge — Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    # Safari — Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]

_ACCEPT_LANGUAGES = [
    "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "es-MX,es;q=0.9,en;q=0.8",
    "es-419,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "es-MX,es-419;q=0.9,es;q=0.8",
    "es,en-US;q=0.9,en;q=0.8",
]

_REFERERS = [
    "https://www.google.com.mx/",
    "https://www.google.com/",
    "https://www.mercadolibre.com.mx/",
    "https://www.mercadolibre.com.mx/ofertas",
    "",  # Sometimes no referer (direct visit)
]


class MeliService:
    """
    Scrapes MercadoLibre product pages directly via HTTP.
    Extracts structured data from the JSON-LD <script> tags embedded in the
    public HTML — no API keys or OAuth tokens required.

    Anti-blocking measures:
    - Rotating User-Agent pool (15+ realistic browsers)
    - Randomized Accept-Language / Referer headers
    - Persistent session with cookie jar (looks like a real browser session)
    - Randomized delays with jitter between requests
    - Exponential backoff on rate-limits
    """

    def __init__(self):
        # Persistent session — keeps cookies across requests like a real browser
        self._session = requests.Session()
        self._backoff_until = 0  # timestamp when backoff expires

    def _random_headers(self) -> dict:
        """Generate a fresh set of randomised browser-like headers."""
        ua = random.choice(_USER_AGENTS)
        is_chrome = "Chrome" in ua and "Edg" not in ua

        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": random.choice(_ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
            "Sec-Fetch-User": "?1",
            "Cache-Control": random.choice(["max-age=0", "no-cache", ""]),
        }

        # Add realistic Referer sometimes
        referer = random.choice(_REFERERS)
        if referer:
            headers["Referer"] = referer

        # Chrome sends sec-ch-ua headers
        if is_chrome:
            ver = re.search(r"Chrome/(\d+)", ua)
            if ver:
                v = ver.group(1)
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "Google Chrome";v="{v}", "Not-A.Brand";v="8"'
                headers["sec-ch-ua-mobile"] = "?0"
                headers["sec-ch-ua-platform"] = '"Windows"' if "Windows" in ua else '"macOS"' if "Mac" in ua else '"Linux"'

        return headers

    def _wait_with_jitter(self, base_delay: float):
        """Sleep for base_delay ± 50% random jitter (looks more human)."""
        jitter = base_delay * random.uniform(-0.5, 0.5)
        actual = max(0.5, base_delay + jitter)
        time.sleep(actual)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_id_from_url(url: str):
        """
        Extract the MercadoLibre item ID from a URL.
        https://articulo.mercadolibre.com.mx/MLM-2471959791-... → MLM2471959791
        https://www.mercadolibre.com.mx/.../up/MLMU3075254897  → MLMU3075254897
        """
        # Match MLMU (user products) or MLM (standard items)
        match = re.search(r"(MLMU|MLM)-?(\d+)", url, re.IGNORECASE)
        if match:
            return f"{match.group(1).upper()}{match.group(2)}"
        return None

    @staticmethod
    def _format_url(item_id: str) -> str:
        """
        MLM2471959791  → https://articulo.mercadolibre.com.mx/MLM-2471959791
        MLMU3075254897 → https://articulo.mercadolibre.com.mx/MLMU-3075254897
        """
        upper = item_id.upper()
        if "-" not in item_id:
            if upper.startswith("MLMU"):
                item_id = f"MLMU-{item_id[4:]}"
            elif upper.startswith("MLM"):
                item_id = f"MLM-{item_id[3:]}"
        return f"https://articulo.mercadolibre.com.mx/{item_id}"

    # ------------------------------------------------------------------
    # Core scraping
    # ------------------------------------------------------------------

    def scrape_item(self, item_id: str, original_url: str = None) -> dict | None:
        """
        Fetch the public product page and return a normalised dict:
        {id, title, price, original_price, currency_id, permalink, thumbnail, condition}
        """
        # Respect backoff
        if time.time() < self._backoff_until:
            wait = self._backoff_until - time.time()
            logger.info(f"⏳ Backoff active, waiting {wait:.0f}s before next request...")
            time.sleep(wait)

        urls_to_try = []
        if original_url and "articulo." in original_url:
            urls_to_try.append(original_url)
        urls_to_try.append(self._format_url(item_id))

        for page_url in urls_to_try:
            try:
                headers = self._random_headers()
                logger.info(f"Scraping {page_url} ...")
                resp = self._session.get(
                    page_url, headers=headers, timeout=15, allow_redirects=True
                )

                if resp.status_code == 429:
                    # Explicit rate limit — back off exponentially
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    self._backoff_until = time.time() + retry_after
                    logger.warning(f"⚠️ HTTP 429 — backing off {retry_after}s")
                    return None

                if resp.status_code != 200:
                    if resp.status_code == 404 and len(resp.text) > 10000:
                        logger.info(f"Got 404 but page has content ({len(resp.text)} bytes). Parsing anyway...")
                    else:
                        logger.warning(f"HTTP {resp.status_code} for {page_url}, trying next...")
                        continue

                # --- Detect captcha / rate-limit page --------------------
                if "<title>Mercado Libre</title>" in resp.text and len(resp.text) > 50000:
                    # Soft rate-limit: exponential backoff (30s → 60s → 120s)
                    backoff = min(300, 30 * (2 ** random.randint(0, 2)))
                    self._backoff_until = time.time() + backoff
                    logger.warning(
                        f"⚠️ Rate-limited (challenge page). "
                        f"Backing off {backoff}s."
                    )
                    return None

                # --- Extract JSON-LD blocks -----------------------------
                blocks = re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    resp.text,
                    re.DOTALL,
                )

                for raw in blocks:
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    item_type = data.get("@type", "")
                    if item_type != "Product" and not (
                        isinstance(item_type, list) and "Product" in item_type
                    ):
                        continue

                    offers = data.get("offers", {})
                    price = offers.get("price")
                    if not price:
                        continue

                    image = data.get("image", "")
                    if isinstance(image, list):
                        image = image[0] if image else ""

                    result = {
                        "id": item_id,
                        "title": data.get("name", ""),
                        "price": float(price),
                        "original_price": None,
                        "currency_id": offers.get("priceCurrency", "MXN"),
                        "permalink": data.get("url") or resp.url,
                        "thumbnail": image,
                        "condition": "new",
                        "source": "mercadolibre",
                    }

                    logger.info(
                        f"✅ {item_id}: {result['title'][:60]}  ${result['price']}"
                    )
                    return result

                # --- Fallback: meta tags --------------------------------
                logger.warning(f"No Product JSON-LD on {page_url}. Trying meta tags...")
                meta_result = self._parse_meta_tags(resp.text, item_id, resp.url)
                if meta_result:
                    return meta_result

            except Exception as e:
                logger.error(f"Error scraping {page_url}: {e}")
                continue

        logger.error(f"All URLs failed for {item_id}")
        return None

    def _parse_meta_tags(self, html: str, item_id: str, final_url: str) -> dict | None:
        """Last-resort extraction from <meta> tags or price spans."""
        title_m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        price_m = re.search(r'"price":\s*([\d.]+)', html)

        if title_m and price_m:
            return {
                "id": item_id,
                "title": title_m.group(1),
                "price": float(price_m.group(1)),
                "original_price": None,
                "currency_id": "MXN",
                "permalink": final_url,
                "thumbnail": "",
                "condition": "new",
                "source": "mercadolibre",
            }
        return None

    # ------------------------------------------------------------------
    # Batch helpers (for update_tracked)
    # ------------------------------------------------------------------

    def scrape_items(self, item_ids: list[str], delay: float = 3.0) -> list[dict]:
        """
        Scrape multiple items with human-like timing.
        - Random delay 1.5s–4.5s between requests (jitter around base delay)
        - Stops after 3 consecutive failures (likely rate-limited)
        - Resets session cookies every ~20 items (new "browsing session")
        """
        results = []
        consecutive_failures = 0

        for idx, iid in enumerate(item_ids):
            # Reset session every ~20 items to look like a new visitor
            if idx > 0 and idx % 20 == 0:
                logger.info(f"🔄 Rotating session (clearing cookies) at item {idx}")
                self._session.cookies.clear()

            item = self.scrape_item(iid)
            if item:
                results.append(item)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.warning(
                        f"⚠️ {consecutive_failures} consecutive failures — "
                        f"likely rate-limited. Stopping batch early. "
                        f"Scraped {len(results)}/{len(item_ids)} items."
                    )
                    break

            if idx < len(item_ids) - 1:
                self._wait_with_jitter(delay)

        return results


# -----------------------------------------------------------------------
# DB persistence (unchanged logic from before)
# -----------------------------------------------------------------------

def process_products(products: list[dict], db_session):
    alerts = []
    processed_count = 0

    MIN_DROP_PCT = 25
    MIN_DROP_AMOUNT = 500

    for p in products:
        try:
            sku = p["id"]
            url = p["permalink"]
            price = p["price"]
            name = p["title"]

            if not url:
                continue

            db_product = (
                db_session.query(Product)
                .filter(Product.sku == sku, Product.source == "mercadolibre")
                .first()
            )

            if db_product:
                old_price = db_product.current_price

                if price < old_price:
                    drop = old_price - price
                    pct = (drop / old_price) * 100

                    if pct >= MIN_DROP_PCT or drop >= MIN_DROP_AMOUNT:
                        alerts.append(
                            {
                                "source": "mercadolibre",
                                "title": name,
                                "price": price,
                                "old_price": old_price,
                                "discount_pct": round(pct, 1),
                                "url": url,
                                "sku": sku,
                            }
                        )

                if abs(price - old_price) > 0.1:
                    db_product.current_price = price
                    db_session.add(
                        PriceHistory(
                            product_id=db_product.id,
                            price=price,
                            timestamp=datetime.utcnow(),
                        )
                    )

                db_product.last_checked = datetime.utcnow()
                db_product.url = url

            else:
                new_prod = Product(
                    name=name,
                    sku=sku,
                    url=url,
                    current_price=price,
                    source="mercadolibre",
                    last_checked=datetime.utcnow(),
                )
                db_session.add(new_prod)
                db_session.flush()
                db_session.add(
                    PriceHistory(
                        product_id=new_prod.id,
                        price=price,
                        timestamp=datetime.utcnow(),
                    )
                )

            processed_count += 1

        except Exception as e:
            logger.error(f"Error saving product {p.get('id')}: {e}")
            continue

    try:
        db_session.commit()
    except Exception as e:
        logger.error(f"Commit error: {e}")
        db_session.rollback()

    return alerts, processed_count


# -----------------------------------------------------------------------
# Main entry point (used by tasks.py and add_meli_url.py)
# -----------------------------------------------------------------------

def get_meli_deals(query="update_tracked"):
    """
    - URL or ID  → scrape that single item and save it.
    - 'update_tracked' → re-scrape every existing Meli item in the DB.
    """
    service = MeliService()
    session = SessionLocal()

    try:
        # 1. Single item by URL or ID
        item_id = service.extract_id_from_url(query)
        if not item_id and query.upper().startswith("MLM"):
            item_id = query

        if item_id:
            logger.info(f"Scraping single item: {item_id}")
            # Pass original URL so it's tried first (covers /p/ style links)
            original_url = query if query.startswith("http") else None
            item_data = service.scrape_item(item_id, original_url=original_url)
            if item_data:
                return process_products([item_data], session)
            return [], 0

        # 2. Batch update
        if query == "update_tracked":
            tracked = (
                session.query(Product)
                .filter(Product.source == "mercadolibre")
                .all()
            )
            if not tracked:
                logger.info("No tracked Meli items to update.")
                return [], 0

            ids = [p.sku for p in tracked if p.sku]
            logger.info(f"Updating {len(ids)} tracked Meli items via web scraping...")
            scraped = service.scrape_items(ids)
            if scraped:
                return process_products(scraped, session)
            return [], 0

        logger.warning(f"Unknown query '{query}'. Pass a URL, item ID, or 'update_tracked'.")
        return [], 0

    finally:
        session.close()
