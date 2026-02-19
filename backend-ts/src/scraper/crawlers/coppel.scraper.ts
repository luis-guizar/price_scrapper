import { Injectable, Logger } from '@nestjs/common';
import { CheerioCrawler, createCheerioRouter, CheerioCrawlingContext, RequestQueue } from 'crawlee';
import { ProductRepository, ScrapedProduct } from '../repositories/product.repository';

@Injectable()
export class CoppelScraper {
    private readonly logger = new Logger(CoppelScraper.name);
    private readonly baseUrl = 'https://www.coppel.com';

    constructor(private readonly productRepository: ProductRepository) { }

    async scrapeCategory(url: string): Promise<ScrapedProduct[]> {
        const categoryLabel = url.split('/').pop()?.substring(0, 20) || 'category';
        this.logger.log(`🚀 Starting Coppel scrape for: ${categoryLabel}`);
        let totalScraped = 0;
        const allProducts: ScrapedProduct[] = [];

        // Unique queue for isolation
        const uniqueQueueId = `coppel_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        const requestQueue = await RequestQueue.open(uniqueQueueId);

        const router = createCheerioRouter();

        // Handler for all pages (main + pagination)
        router.addDefaultHandler(async ({ $, request, log }: CheerioCrawlingContext) => {
            const currentUrl = request.url;
            const pageInfo = currentUrl.includes('beginIndex=')
                ? `page ${Math.floor(parseInt(currentUrl.split('beginIndex=')[1]) / 24) + 1}`
                : 'main page';

            log.info(`📄 Processing ${pageInfo}...`);

            try {
                // 3. Extract __NEXT_DATA__ directly from HTML string
                const nextDataScript = $('#__NEXT_DATA__').html();

                if (!nextDataScript) {
                    log.warning(`⚠️ No __NEXT_DATA__ found on ${currentUrl}`);
                    return;
                }

                const nextData = JSON.parse(nextDataScript);

                // 4. Extract Products from JSON
                const products = this.extractProductsFromJson(nextData);

                if (products.length > 0) {
                    log.info(`✅ Found ${products.length} products on ${pageInfo}`);
                    // Use a more gentle upsert if needed, but bulkUpsert is usually fine
                    await this.productRepository.bulkUpsert(products);
                    totalScraped += products.length;
                    allProducts.push(...products);
                } else {
                    log.warning(`⚠️ No products found in JSON on ${pageInfo}`);
                }

                // 5. Handle Pagination (Only on the first page/job)
                // If the URL doesn't have 'beginIndex', we assume it's the main page and calculate total pages
                if (!currentUrl.includes('beginIndex=')) {
                    const totalCount = this.extractTotalCount(nextData);
                    log.info(`📅 Total products in category: ${totalCount}`);

                    if (totalCount > 24) {
                        const pageSize = 24;
                        // Limit pages to prevent infinite loops, but allow deep scraping
                        const maxPages = Math.min(Math.ceil(totalCount / pageSize), 200);

                        log.info(`🔗 Enqueuing ${maxPages - 1} pagination pages...`);

                        for (let p = 2; p <= maxPages; p++) {
                            const beginIndex = (p - 1) * pageSize;
                            const nextUrl = currentUrl.includes('?')
                                ? `${currentUrl}&beginIndex=${beginIndex}`
                                : `${currentUrl}?beginIndex=${beginIndex}`;

                            await requestQueue.addRequest({ url: nextUrl });
                        }
                    }
                }

            } catch (e) {
                log.error(`❌ Error processing ${currentUrl}: ${e.message}`);
            }
        });

        const crawler = new CheerioCrawler({
            requestHandler: router,
            requestQueue,
            maxConcurrency: 10, // Increased concurrency for faster scraping with lightweight Cheerio
            // Cheerio is just HTTP requests + HTML parsing, very low RAM
            requestHandlerTimeoutSecs: 60,
        });

        // Add the initial request
        await requestQueue.addRequest({ url });

        await crawler.run();
        await requestQueue.drop();

        this.logger.log(`✅ Finished: Scraped ${totalScraped} products total for ${categoryLabel}.`);
        return allProducts;
    }

    private extractTotalCount(nextData: any): number {
        try {
            const pageProps = nextData?.props?.pageProps || {};
            return pageProps?.PLPProducts?.totalCount || 0;
        } catch (e) {
            return 0;
        }
    }

    private extractProductsFromJson(nextData: any): ScrapedProduct[] {
        const extracted: ScrapedProduct[] = [];
        try {
            const pageProps = nextData?.props?.pageProps || {};
            let productsList = [];

            // Try PLPProducts
            if (pageProps.PLPProducts && Array.isArray(pageProps.PLPProducts.products)) {
                productsList = pageProps.PLPProducts.products;
            } else {
                // Fallback: Apollo State logic from Python
                const apolloState = pageProps.apolloState ||
                    nextData?.props?.apolloState ||
                    pageProps.appData?.apolloState;

                if (apolloState) {
                    for (const key in apolloState) {
                        if (key.startsWith("LucidProduct:") && typeof apolloState[key] === 'object') {
                            productsList.push(apolloState[key]);
                        }
                    }
                }
            }

            for (const p of productsList) {
                const item = this.parseSingleProduct(p);
                if (item) {
                    extracted.push(item);
                }
            }
        } catch (e) {
            this.logger.warn(`Error extraction JSON products: ${e.message}`);
        }
        return extracted;
    }

    private parseSingleProduct(p: any): ScrapedProduct | null {
        try {
            const name = p.name;
            const sku = p.sku || p.partNumber;
            const urlSlug = p.url || p.seo_token || p.href;

            if (!urlSlug || !name) return null;

            let productUrl = urlSlug;
            if (!productUrl.startsWith('http')) {
                // Ensure there is a slash
                const path = productUrl.startsWith('/') ? productUrl : `/${productUrl}`;
                productUrl = `${this.baseUrl}${path}`;
            }

            // Price Logic
            const priceInfo = p.price || {};

            const parsePrice = (val: any) => {
                if (typeof val === 'number') return val;
                if (typeof val === 'string') {
                    const cleaned = val.replace(/,/g, '').replace('$', '').trim();
                    const parsed = parseFloat(cleaned);
                    return isNaN(parsed) ? 0 : parsed;
                }
                return 0;
            };

            const pSales = parsePrice(priceInfo.salesPrice || p.salesPrice || priceInfo.formattedPriceValue);
            const pList = parsePrice(priceInfo.listPrice || p.listPrice || priceInfo.formattedListPrice);
            const pDisc = parsePrice(priceInfo.discountedPrice || p.discountedPrice);

            // Filter out 0s
            const candidates = [pDisc, pSales, pList].filter(x => x > 0);
            if (candidates.length === 0) return null;

            const currentPrice = Math.min(...candidates);
            const originalPrice = Math.max(...candidates);

            let image = p.thumbnail || p.fullImage || p.image;
            if (Array.isArray(image)) {
                image = image[0];
            }

            return {
                name,
                sku,
                url: productUrl,
                current_price: currentPrice,
                original_price: originalPrice,
                source: 'coppel',
                image: typeof image === 'string' ? image : undefined,
            };
        } catch (e) {
            return null;
        }
    }
}
