import { Injectable, Logger } from '@nestjs/common';
import { PlaywrightCrawler, createPlaywrightRouter, PlaywrightCrawlingContext, RequestQueue } from 'crawlee';
import { ProductRepository, ScrapedProduct } from '../repositories/product.repository';
import { ScrapeProgress } from '../scraper.types';

@Injectable()
export class MeliScraper {
    private readonly logger = new Logger(MeliScraper.name);

    constructor(private readonly productRepository: ProductRepository) { }

    async scrapeCategory(url: string, progress?: ScrapeProgress): Promise<ScrapedProduct[]> {
        const categoryLabel = url.split('/').pop()?.substring(0, 20) || 'meli-category';
        this.logger.log(`🚀 Starting MercadoLibre scrape for: ${categoryLabel}`);
        let totalScraped = 0;
        const allProducts: ScrapedProduct[] = [];

        // Unique queue for isolation
        const uniqueQueueId = `meli_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        const requestQueue = await RequestQueue.open(uniqueQueueId);

        const router = createPlaywrightRouter();

        router.addDefaultHandler(async ({ page, request, log }: PlaywrightCrawlingContext) => {
            const currentUrl = request.url;
            log.info(`📄 Processing page: ${currentUrl}`);

            try {
                // Wait for product cards to load
                await page.waitForSelector('li.ui-search-layout__item', { timeout: 15000 }).catch(() => {
                    log.warning(`⚠️ No items found on ${currentUrl} (Timeout)`);
                });

                // Extract products
                const products = await page.$$eval('li.ui-search-layout__item', (items) => {
                    return items.map((el) => {
                        const titleEl = el.querySelector('h3') || el.querySelector('h2');
                        const priceEl = el.querySelector('.andes-money-amount__fraction');
                        const urlEl = el.querySelector('a');

                        if (!titleEl || !priceEl || !urlEl) return null;

                        const name = titleEl.textContent?.trim() || '';
                        let priceStr = priceEl.textContent?.trim() || '0';
                        priceStr = priceStr.replace(/,/g, '');
                        const price = parseFloat(priceStr);

                        let productUrl = urlEl.getAttribute('href') || '';
                        // Clean up URL parameters (remove tracking stuff)
                        productUrl = productUrl.split('#')[0].split('?')[0];

                        // Extract ID from URL (e.g. https://articulo.mercadolibre.com.mx/MLM-1234567...)
                        const match = productUrl.match(/(ML[A-Z]-?\d+)/);
                        const sku = match ? match[1].replace('-', '') : `unknown-${Math.random()}`;

                        if (price > 0 && name) {
                            return { name, sku, url: productUrl, current_price: price, original_price: price, source: 'mercadolibre' };
                        }
                        return null;
                    }).filter(item => item !== null) as any[]; // TypeScript doesn't know about ScrapedProduct here
                });

                if (products.length > 0) {
                    log.info(`✅ Found ${products.length} products`);
                    await this.productRepository.bulkUpsert(products);
                    totalScraped += products.length;
                    allProducts.push(...products);
                    await progress?.onProgress?.(totalScraped);

                    // Restrict max pages to avoid ban from heavy playwright instances and grab most relevant matches
                    const currentDepth = request.userData?.depth || 1;
                    const maxDepth = 4;

                    if (currentDepth >= maxDepth) {
                        log.info(`🛑 Reached max depth limit of ${maxDepth} pages for this category run.`);
                    } else if (totalScraped >= 1000) {
                        log.info(`🛑 Reached max limit of 1000 items for this category run.`);
                    } else {
                        const hasNextPage = await page.evaluate(() => {
                            const nextBtn = document.querySelector('.andes-pagination__button--next');
                            return nextBtn && !nextBtn.classList.contains('andes-pagination__button--disabled');
                        });

                        if (hasNextPage) {
                            const urlObj = new URL(currentUrl);
                            let nextUrlStr = '';

                            const desdeMatch = urlObj.pathname.match(/_Desde_(\d+)/);
                            if (desdeMatch) {
                                const currentDesde = parseInt(desdeMatch[1], 10);
                                const nextDesde = currentDesde + 48;
                                urlObj.pathname = urlObj.pathname.replace(`_Desde_${currentDesde}`, `_Desde_${nextDesde}`);
                            } else {
                                urlObj.pathname = urlObj.pathname + '_Desde_49';
                            }

                            nextUrlStr = urlObj.toString();
                            log.info(`🔗 Found next page, enqueuing (Depth: ${currentDepth + 1}): ${nextUrlStr}`);
                            await requestQueue.addRequest({ url: nextUrlStr, userData: { depth: currentDepth + 1 } });
                        } else {
                            log.info(`🛑 Reached the last page of this category.`);
                        }
                    }
                } else {
                    log.warning(`⚠️ No products extracted from ${currentUrl}`);
                }
            } catch (e: any) {
                log.error(`❌ Error processing ${currentUrl}: ${e.message}`);
                await progress?.onLog?.(`❌ Error on ${currentUrl}: ${e.message}`);
            }
        });

        const crawler = new PlaywrightCrawler({
            requestHandler: router,
            requestQueue,
            maxConcurrency: 2, // Playwright is heavy, keep concurrency low
            maxRequestRetries: 1,
            navigationTimeoutSecs: 30, // Datadome challenges can slow down navigation
            browserPoolOptions: {
                useFingerprints: true // Helps avoid basic bot detection
            },
            launchContext: {
                launchOptions: {
                    headless: true, // you can set this to false for debugging
                },
            },
            preNavigationHooks: [
                async ({ page }) => {
                    // Block unnecessary resources to speed up and reduce RAM
                    await page.route('**/*', (route) => {
                        const type = route.request().resourceType();
                        if (['image', 'media', 'font', 'stylesheet'].includes(type)) {
                            route.abort();
                        } else {
                            route.continue();
                        }
                    });
                    await page.setExtraHTTPHeaders({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    });
                }
            ]
        });

        await requestQueue.addRequest({ url, userData: { depth: 1 } });
        await crawler.run();
        await requestQueue.drop();

        this.logger.log(`✅ Finished: Scraped ${totalScraped} products total for ${categoryLabel}.`);
        return allProducts;
    }
}
