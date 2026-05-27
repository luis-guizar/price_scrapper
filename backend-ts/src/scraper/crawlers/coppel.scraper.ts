import { Injectable, Logger } from '@nestjs/common';
import {
  CheerioCrawler,
  createCheerioRouter,
  CheerioCrawlingContext,
  RequestQueue,
} from 'crawlee';
import {
  ProductRepository,
  ScrapedProduct,
} from '../repositories/product.repository';
import { ScrapeProgress } from '../scraper.types';
import { ELECTRONICS_RULES } from '../utils/price-guard';
import { PriceValidationService } from '../services/price-validation.service';

@Injectable()
export class CoppelScraper {
  private readonly logger = new Logger(CoppelScraper.name);
  private readonly baseUrl = 'https://www.coppel.com';

  constructor(
    private readonly productRepository: ProductRepository,
    private readonly priceValidator: PriceValidationService,
  ) {}

  async scrapeCategory(
    url: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    const categoryLabel = url.split('/').pop()?.substring(0, 20) || 'category';
    this.logger.log(`🚀 Starting Coppel scrape for: ${categoryLabel}`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    // Unique queue for isolation
    const uniqueQueueId = `coppel_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const requestQueue = await RequestQueue.open(uniqueQueueId);

    const router = createCheerioRouter();

    // Handler for all pages (main + pagination)
    router.addDefaultHandler(
      async ({ $, request, log }: CheerioCrawlingContext) => {
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
          const { extracted: products, rawCount } =
            this.extractProductsFromJson(nextData);

          if (products.length > 0) {
            log.info(
              `✅ Found ${products.length} valid products on ${pageInfo}`,
            );
            const validated = await this.priceValidator.validateBatch(
              products,
              ELECTRONICS_RULES,
            );
            log.debug(`⏳ Starting bulkUpsert for ${validated.length} items...`);
            await this.productRepository.bulkUpsert(validated);
            log.debug(`✅ Finished bulkUpsert for ${pageInfo}`);
            totalScraped += validated.length;
            allProducts.push(...validated);
            await progress?.onProgress?.(totalScraped);
          } else {
            if (rawCount === 0) {
              log.info(`🏁 Reached empty catalog data on ${pageInfo}`);
            } else {
              log.debug(
                `⚠️ Kept 0 of ${rawCount} raw products on ${pageInfo} (all filtered out)`,
              );
            }
          }

          // 5. Dynamic Sliding Window Pagination
          if (rawCount > 0) {
            const pageSize = 24;
            const MAX_PAGES = 300; // Hard safety cap
            const WINDOW_SIZE = 2; // Match maxConcurrency

            const isMainPage = !currentUrl.includes('beginIndex=');
            const match = currentUrl.match(/beginIndex=(\d+)/);
            const p = match ? Math.floor(parseInt(match[1]) / pageSize) + 1 : 1;

            const baseUrl = currentUrl
              .split('beginIndex=')[0]
              .replace(/[?&]$/, '');
            const separator = baseUrl.includes('?') ? '&' : '?';
            let expectedMax = request.userData?.expectedMax || MAX_PAGES;

            if (isMainPage) {
              const totalCount = this.extractTotalCount(nextData);
              expectedMax = Math.min(
                Math.ceil(totalCount / pageSize),
                MAX_PAGES,
              );
              log.info(
                `📅 Reported total items: ${totalCount} (Approx ${expectedMax} pages)`,
              );

              const enqueueUpTo = Math.min(WINDOW_SIZE, expectedMax);
              if (enqueueUpTo > 1) {
                log.info(
                  `🔗 Sliding window dynamically starting up to page ${enqueueUpTo}...`,
                );
                const promises = [];
                for (let i = 2; i <= enqueueUpTo; i++) {
                  promises.push(
                    requestQueue.addRequest({
                      url: `${baseUrl}${separator}beginIndex=${(i - 1) * pageSize}`,
                      userData: { expectedMax },
                    }),
                  );
                }
                log.debug(
                  `⏳ Waiting on RequestQueue for ${promises.length} items...`,
                );
                await Promise.all(promises);
                log.debug(`✅ Enqueued ${promises.length} items`);
              }

              const nextP = p + WINDOW_SIZE;
              if (nextP <= expectedMax) {
                log.debug(`⏳ Enqueuing forward slide page ${nextP}...`);
                await requestQueue.addRequest({
                  url: `${baseUrl}${separator}beginIndex=${(nextP - 1) * pageSize}`,
                  userData: { expectedMax },
                });
              }
            } else {
              const nextP = p + WINDOW_SIZE;
              if (nextP <= expectedMax) {
                log.debug(`⏳ Enqueuing forward slide page ${nextP}...`);
                await requestQueue.addRequest({
                  url: `${baseUrl}${separator}beginIndex=${(nextP - 1) * pageSize}`,
                  userData: { expectedMax },
                });
              }
            }
          }
        } catch (e) {
          log.error(`❌ Error processing ${currentUrl}: ${e.message}`);
          await progress?.onLog?.(`❌ Error on ${currentUrl}: ${e.message}`);
        }
      },
    );

    const crawler = new CheerioCrawler({
      requestHandler: router,
      requestQueue,
      maxConcurrency: 2, // Reduced concurrency to save RAM, JSON loads can be large
      // Cheerio is just HTTP requests + HTML parsing, but large __NEXT_DATA__ json causes memory spikes
      requestHandlerTimeoutSecs: 60,
    });

    // Add the initial request
    await requestQueue.addRequest({ url });

    await crawler.run();
    await requestQueue.drop();

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products total for ${categoryLabel}.`,
    );
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

  private extractProductsFromJson(nextData: any): {
    extracted: ScrapedProduct[];
    rawCount: number;
  } {
    const extracted: ScrapedProduct[] = [];
    let rawCount = 0;
    try {
      const pageProps = nextData?.props?.pageProps || {};
      let productsList = [];

      // Try PLPProducts
      if (
        pageProps.PLPProducts &&
        Array.isArray(pageProps.PLPProducts.products)
      ) {
        productsList = pageProps.PLPProducts.products;
      } else {
        // Fallback: Apollo State logic from Python
        const apolloState =
          pageProps.apolloState ||
          nextData?.props?.apolloState ||
          pageProps.appData?.apolloState;

        if (apolloState) {
          for (const key in apolloState) {
            if (
              key.startsWith('LucidProduct:') &&
              typeof apolloState[key] === 'object'
            ) {
              productsList.push(apolloState[key]);
            }
          }
        }
      }

      rawCount = productsList.length;

      for (const p of productsList) {
        const item = this.parseSingleProduct(p);
        if (item) {
          extracted.push(item);
        }
      }
    } catch (e) {
      this.logger.warn(`Error extraction JSON products: ${e.message}`);
    }
    return { extracted, rawCount };
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

      // Exclude marketplace/external sellers
      if (productUrl.toLowerCase().includes('-mkp-')) {
        return null;
      }
      if (name.toLowerCase().includes('venta internacional')) {
        return null;
      }
      if (p.mpSellerName && !p.mpSellerName.toLowerCase().includes('coppel')) {
        return null;
      }
      if (p.sellerId !== undefined && p.sellerId !== '0') {
        return null;
      }
      if (p.variantTypes && p.variantTypes.isMarketplace === true) {
        return null;
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

      const pSales = parsePrice(
        priceInfo.salesPrice || p.salesPrice || priceInfo.formattedPriceValue,
      );
      const pList = parsePrice(
        priceInfo.listPrice || p.listPrice || priceInfo.formattedListPrice,
      );
      const pDisc = parsePrice(priceInfo.discountedPrice || p.discountedPrice);

      // Filter out 0s
      const candidates = [pDisc, pSales, pList].filter((x) => x > 0);
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
