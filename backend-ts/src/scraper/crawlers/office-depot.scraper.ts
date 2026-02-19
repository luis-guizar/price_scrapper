import { Injectable, Logger } from '@nestjs/common';
import { PlaywrightCrawler, Dataset, createPlaywrightRouter, PlaywrightCrawlingContext, RequestQueue } from 'crawlee';
import { Page } from 'playwright';
import { ProductRepository, ScrapedProduct } from '../repositories/product.repository';

@Injectable()
export class OfficeDepotScraper {
    private readonly logger = new Logger(OfficeDepotScraper.name);
    private readonly maxPages = 10;
    private readonly baseUrl = 'https://www.officedepot.com.mx';

    constructor(private readonly productRepository: ProductRepository) { }

    async scrapeCategory(url: string): Promise<ScrapedProduct[]> {
        const categoryLabel = url.split('/').pop()?.substring(0, 20) || 'category';
        this.logger.log(`🚀 Starting Office Depot scrape for: ${categoryLabel}`);
        let totalScraped = 0;
        const allProducts: ScrapedProduct[] = [];

        // Create a unique RequestQueue for this job to ensure isolation
        const uniqueQueueId = `od_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        const requestQueue = await RequestQueue.open(uniqueQueueId);

        const router = createPlaywrightRouter();

        // Handler for category pages
        router.addDefaultHandler(async ({ page, request, log }: PlaywrightCrawlingContext) => {
            const currentUrl = request.url;
            const pageNumMatch = currentUrl.match(/page=(\d+)/);
            const pageInfo = pageNumMatch ? `page ${parseInt(pageNumMatch[1]) + 1}` : 'main page';

            log.info(`📄 Processing ${pageInfo}...`);

            // Extract products
            const products = await this.extractProductsFromPage(page, currentUrl);

            if (products.length > 0) {
                log.info(`✅ Found ${products.length} products on ${pageInfo}`);
                await this.productRepository.bulkUpsert(products);
                totalScraped += products.length;
                allProducts.push(...products);
            } else {
                log.warning(`⚠️ No products found on ${pageInfo}`);
            }
        });

        const crawler = new PlaywrightCrawler({
            requestHandler: router,
            requestQueue, // Use our isolated queue
            maxConcurrency: 1, // Stay safe on RAM
            headless: true,
            browserPoolOptions: {
                useFingerprints: true,
            },
            preNavigationHooks: [
                async ({ page }) => {
                    await page.route('**/*', (route) => {
                        const resourceType = route.request().resourceType();
                        if (['image', 'media', 'font', 'stylesheet'].includes(resourceType)) {
                            route.abort();
                        } else {
                            route.continue();
                        }
                    });
                },
            ],
            requestHandlerTimeoutSecs: 90,
            navigationTimeoutSecs: 120,
        });

        // Enqueue URLs to the specific queue
        for (let i = 0; i < this.maxPages; i++) {
            const pageUrl = url.includes('?')
                ? `${url}&page=${i}`
                : `${url}?q=%3Arelevance&page=${i}`;
            await requestQueue.addRequest({ url: pageUrl });
        }

        await crawler.run(); // Run without args, it uses the attached queue
        await requestQueue.drop();

        this.logger.log(`✅ Finished: Scraped ${totalScraped} products total for ${categoryLabel}.`);
        return allProducts;
    }

    private async extractProductsFromPage(page: Page, url: string): Promise<ScrapedProduct[]> {
        const products: ScrapedProduct[] = [];

        try {
            // Wait for network/content
            await page.waitForLoadState('domcontentloaded');
            await page.waitForTimeout(3000); // 3s wait as in Python

            const content = await page.content();

            // Regex Extraction Strategy
            // Python: re.search(r"'impressions'\s*:\s*\[(.*?)\]", content, re.DOTALL)
            const impressionsMatch = content.match(/'impressions'\s*:\s*\[(.*?)\]/s); // /s for DOTALL

            if (impressionsMatch && impressionsMatch[1]) {
                const impressionsStr = impressionsMatch[1];
                // Match individual objects: { ... }
                const itemMatches = impressionsStr.match(/\{[^{}]*\}/g);

                if (itemMatches) {
                    for (const itemStr of itemMatches) {
                        try {
                            const idMatch = itemStr.match(/'id'\s*:\s*'([^']*)'/);
                            const nameMatch = itemStr.match(/'name'\s*:\s*'([^']*)'/);
                            const priceMatch = itemStr.match(/'price'\s*:\s*'([^']*)'/);

                            if (idMatch && nameMatch) {
                                const pid = idMatch[1];
                                const name = nameMatch[1];
                                let priceRaw = priceMatch ? priceMatch[1] : '0';
                                priceRaw = priceRaw.replace(/,/g, '');
                                const price = parseFloat(priceRaw) || 0;

                                const productUrl = `${this.baseUrl}/officedepot/en/p/${pid}`;

                                if (pid && name && price > 0) {
                                    products.push({
                                        name,
                                        sku: pid,
                                        url: productUrl,
                                        current_price: price,
                                        original_price: price, // Logic will be handled in DB upsert
                                        source: 'officedepot',
                                    });
                                }
                            }
                        } catch (e) {
                            // ignore malformed items
                        }
                    }
                }
            }

            // Fallback: DataLayer
            if (products.length === 0) {
                const dataLayer = await page.evaluate(() => (window as any).dataLayer);
                if (Array.isArray(dataLayer)) {
                    for (const item of dataLayer) {
                        if (item.impressions && Array.isArray(item.impressions)) {
                            for (const prod of item.impressions) {
                                try {
                                    const pid = prod.id;
                                    const name = prod.name;
                                    let priceRaw = String(prod.price || '0');
                                    priceRaw = priceRaw.replace(/,/g, '');
                                    const price = parseFloat(priceRaw) || 0;
                                    const productUrl = `${this.baseUrl}/officedepot/en/p/${pid}`;

                                    if (pid && name && price > 0) {
                                        products.push({
                                            name,
                                            sku: pid,
                                            url: productUrl,
                                            current_price: price,
                                            original_price: price,
                                            source: 'officedepot',
                                        });
                                    }
                                } catch (e) { }
                            }
                        }
                    }
                }
            }

        } catch (e) {
            this.logger.error(`Error extracting products from ${url}: ${e.message}`);
        }

        return products;
    }
}
