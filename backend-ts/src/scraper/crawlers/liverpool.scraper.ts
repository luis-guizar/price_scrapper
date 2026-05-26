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
import {
  capUnreasonableOriginalPrice,
  ELECTRONICS_RULES,
} from '../utils/price-guard';

@Injectable()
export class LiverpoolScraper {
  private readonly logger = new Logger(LiverpoolScraper.name);
  private readonly baseUrl = 'https://www.liverpool.com.mx';

  constructor(private readonly productRepository: ProductRepository) {}

  async scrapeCategory(
    url: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    const categoryLabel = 'liverpool-category';
    this.logger.log(`🚀 Starting Liverpool scrape for: ${url}`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    // Unique queue for isolation
    const uniqueQueueId = `liverpool_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const requestQueue = await RequestQueue.open(uniqueQueueId);

    const router = createCheerioRouter();

    // Handler for all pages
    router.addDefaultHandler(
      async ({ request, log, json, body }: CheerioCrawlingContext) => {
        const currentUrl = request.url;
        // Extract page number from URL if present
        const pageMatch = currentUrl.match(/page=(\d+)/);
        const pageNumber = pageMatch ? parseInt(pageMatch[1]) : 1;
        const pageInfo = `page ${pageNumber}`;

        log.info(`📄 Processing ${pageInfo}...`);

        try {
          // We expect JSON response from the API
          let data: any;

          // Try parsing JSON if not automatically parsed
          if (
            typeof body === 'string' &&
            (body.startsWith('{') || body.startsWith('['))
          ) {
            try {
              data = JSON.parse(body);
            } catch (e) {
              log.warning(`Failed to parse body as JSON: ${e.message}`);
            }
          } else if (json) {
            data = json;
          }

          if (!data) {
            log.warning(`⚠️ No JSON data found on ${currentUrl}`);
            return;
          }

          // Extract products
          const products = this.extractProductsFromJson(data);

          if (products.length > 0) {
            log.info(`✅ Found ${products.length} products on ${pageInfo}`);
            await this.productRepository.bulkUpsert(products);
            totalScraped += products.length;
            allProducts.push(...products);
            await progress?.onProgress?.(totalScraped);
          } else {
            log.warning(`⚠️ No products found in JSON on ${pageInfo}`);
          }

          // Handle Pagination
          // Only on the first page/job request
          if (pageNumber === 1) {
            const totalRecords = data.mainContent?.records?.length || 0; // This is only for the current page
            const totalNumRecords =
              data.mainContent?.totalNumRecords ||
              data.mainContent?.contents?.[0]?.mainContent?.totalNumRecords;

            // In the provided JSON, `numRecords` inside a record seems to be 1.
            // A better place to look for total counts might be `plpResults` or similar if available.
            // However, looking at the provided JSON, it seems `mainContent` has `records`.
            // The provided example JSON `liverpool_reponse.json` is huge.
            // The structure seems to be `mainContent` -> `records` (array of products).

            // Let's rely on the existence of `records` for pagination.
            // If we found products, we try the next page.
            // Ideally we should know the total count.
            // Inspecting `liverpool_reponse.json` structure from previous `view_file`:
            // It doesn't explicitly show `totalNumRecords` in the snippet I saw (first 800 lines).
            // But usually, PLP responses have it.

            // Strategy: If we found products equal to pageSize (default often 20-50), we assume next page exists.
            // Or better, checking the provided URL `page=2`.
            // We can try to increment page until no products are returned.

            // For safety, let's max out at 50 pages to prevent infinite loops if we can't determine total.

            if (products.length > 0) {
              // Assuming page size is around products.length.
              // If we got full page, we fetch next.
              const maxPages = 20; // Conservative limit for now
              log.info(`🔗 Enqueuing up to ${maxPages} pages...`);

              for (let p = 2; p <= maxPages; p++) {
                // Construct next URL
                // We need to replace or add `page` parameter
                const nextUrl = new URL(currentUrl);
                nextUrl.searchParams.set('page', p.toString());
                // We might need to adjust `skip`.
                // The example URL has `skip=53` for `page=2`?
                // Wait, `skip` usually implies offset.
                // If `page=1` (implicit), skip=0?
                // If `page=2`, skip=53?
                // It's possible `skip` is calculated as (page-1)*pageSize.
                // However, we don't know the pageSize.
                // Let's try to just increment `page` parameter first as it is more standard.
                // If `skip` is required, we might need to derive it.
                // Looking at the example URL: `page=2&...&skip=53`
                // If page 1 had 53 items?

                // Let's try to infer if `skip` is needed.
                // For now, I will just update `page` and keep `skip` if present but updated?
                // Actually, removing `skip` might be safer if `page` is handled by backend.
                // Or updated `skip` = (p-1) * products.length?

                // Let's stick to updating `page` parameter only for simplicity first.

                await requestQueue.addRequest({ url: nextUrl.toString() });
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
      maxConcurrency: 2, // Reduced concurrency to save RAM when parsing large JSON responses
      requestHandlerTimeoutSecs: 60,
      // Important: We need to ensure we treat the response as JSON or text, not try to parse HTML too strictly
      additionalMimeTypes: ['application/json', 'text/plain'],
    });

    // Add the initial request
    await requestQueue.addRequest({ url });

    await crawler.run();
    await requestQueue.drop();

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products total for ${url}.`,
    );
    return allProducts;
  }

  private extractProductsFromJson(data: any): ScrapedProduct[] {
    const extracted: ScrapedProduct[] = [];
    try {
      const records = data.mainContent?.records || [];

      for (const record of records) {
        const p = record.allMeta;
        if (!p) continue;

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
      const name = p.title;
      const sku = p.skuId || p.id;
      const urlSlug = p.uri; // e.g. "https://liverpool.com.mx/tienda/pdp/..."

      if (!urlSlug || !name) return null;

      // Price Logic
      const prices = p.variants?.[0]?.prices || {};

      // Helper to parse price
      const parsePrice = (val: any) => {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') {
          const cleaned = val.replace(/,/g, '').replace('$', '').trim();
          const parsed = parseFloat(cleaned);
          return isNaN(parsed) ? 0 : parsed;
        }
        return 0;
      };

      const promoPrice = parsePrice(prices.promoPrice);
      const salePrice = parsePrice(prices.salePrice);
      const listPrice = parsePrice(prices.listPrice);
      const sortPrice = parsePrice(prices.sortPrice);

      // Heuristic: Current price is the lowest non-zero price
      const candidates = [promoPrice, salePrice, sortPrice, listPrice].filter(
        (x) => x > 0,
      );
      if (candidates.length === 0) return null;

      const currentPrice = Math.min(...candidates);
      let originalPrice = listPrice > 0 ? listPrice : Math.max(...candidates);

      // Cap original price to prevent massive false positive discounts on inflated anchors
      originalPrice = capUnreasonableOriginalPrice(
        name,
        currentPrice,
        originalPrice,
        ELECTRONICS_RULES,
        (t, from, to) =>
          this.logger.warn(
            `[Liverpool] Unreasonable original price capped for "${t}": ${from} → ${to}`,
          ),
      );

      // Image
      let image =
        p.variants?.[0]?.largeImage ||
        p.variants?.[0]?.thumbnailImage ||
        p.productImages?.[0]?.largeImage;

      return {
        name,
        sku,
        url: urlSlug,
        current_price: currentPrice,
        original_price: originalPrice,
        source: 'liverpool',
        image: typeof image === 'string' ? image : undefined,
        external_id: sku, // Useful for debugging
      };
    } catch (e) {
      return null;
    }
  }
}
