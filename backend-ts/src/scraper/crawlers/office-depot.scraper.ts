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
import { OFFICE_RULES } from '../utils/price-guard';
import { PriceValidationService } from '../services/price-validation.service';

@Injectable()
export class OfficeDepotScraper {
  private readonly logger = new Logger(OfficeDepotScraper.name);
  private readonly maxPages = 10;
  private readonly baseUrl = 'https://www.officedepot.com.mx';

  constructor(
    private readonly productRepository: ProductRepository,
    private readonly priceValidator: PriceValidationService,
  ) {}

  async scrapeCategory(
    url: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    const categoryLabel = url.split('/').pop()?.substring(0, 20) || 'category';
    this.logger.log(`🚀 Starting Office Depot scrape for: ${categoryLabel}`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    // Create a unique RequestQueue for this job to ensure isolation
    const uniqueQueueId = `od_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const requestQueue = await RequestQueue.open(uniqueQueueId);

    const router = createCheerioRouter();

    // Handler for category pages
    router.addDefaultHandler(
      async ({ request, log, body }: CheerioCrawlingContext) => {
        const currentUrl = request.url;
        const pageNumMatch = currentUrl.match(/page=(\d+)/);
        const pageInfo = pageNumMatch
          ? `page ${parseInt(pageNumMatch[1]) + 1}`
          : 'main page';

        log.info(`📄 Processing ${pageInfo}...`);

        // Extract products using regex from raw body
        const bodyString = typeof body === 'string' ? body : body.toString();
        const products = await this.extractProductsFromBody(
          bodyString,
          currentUrl,
        );

        if (products.length > 0) {
          log.info(`✅ Found ${products.length} products on ${pageInfo}`);
          const validated = await this.priceValidator.validateBatch(
            products,
            OFFICE_RULES,
          );
          await this.productRepository.bulkUpsert(validated);
          totalScraped += validated.length;
          allProducts.push(...validated);
          await progress?.onProgress?.(totalScraped);
        } else {
          log.warning(`⚠️ No products found on ${pageInfo}`);
        }
      },
    );

    const crawler = new CheerioCrawler({
      requestHandler: router,
      requestQueue,
      maxConcurrency: 1, // Reduced to prevent 30s timeouts and WAF blocks
      requestHandlerTimeoutSecs: 60,
    });

    // Enqueue URLs to the specific queue
    for (let i = 0; i < this.maxPages; i++) {
      const pageUrl = url.includes('?')
        ? `${url}&page=${i}`
        : `${url}?q=%3Arelevance&page=${i}`;
      await requestQueue.addRequest({ url: pageUrl });
    }

    await crawler.run();
    await requestQueue.drop();

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products total for ${categoryLabel}.`,
    );
    return allProducts;
  }

  private extractProductsFromBody(body: string, url: string): ScrapedProduct[] {
    const products: ScrapedProduct[] = [];

    try {
      // Regex Extraction Strategy (Same as Python/original Playwright version)
      // It looks for 'impressions' : [...] in the HTML source
      const impressionsMatch = body.match(/'impressions'\s*:\s*\[(.*?)\]/s);

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
                    original_price: price,
                    source: 'officedepot',
                  });
                }
              }
            } catch (e) {}
          }
        }
      }

      // Fallback: search for "dataLayer.push({..." patterns if impressions not found directly
      if (products.length === 0) {
        // Secondary check for common GTM formats in script tags
        const dataLayerItems = body.match(
          /"id"\s*:\s*"([^"]*)",\s*"name"\s*:\s*"([^"]*)",\s*"price"\s*:\s*"([^"]*)"/g,
        );
        if (dataLayerItems) {
          for (const item of dataLayerItems) {
            try {
              const idM = item.match(/"id"\s*:\s*"([^"]*)"/);
              const nameM = item.match(/"name"\s*:\s*"([^"]*)"/);
              const priceM = item.match(/"price"\s*:\s*"([^"]*)"/);

              if (idM && nameM && priceM) {
                const pid = idM[1];
                const name = nameM[1];
                const price = parseFloat(priceM[1].replace(/,/g, '')) || 0;
                if (pid && name && price > 0) {
                  products.push({
                    name,
                    sku: pid,
                    url: `${this.baseUrl}/officedepot/en/p/${pid}`,
                    current_price: price,
                    original_price: price,
                    source: 'officedepot',
                  });
                }
              }
            } catch (e) {}
          }
        }
      }
    } catch (e) {
      this.logger.error(`Error extracting products from ${url}: ${e.message}`);
    }

    return products;
  }
}
