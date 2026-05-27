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
import { BEAUTY_RULES } from '../utils/price-guard';
import { PriceValidationService } from '../services/price-validation.service';

const SEPHORA_BASE_URL = 'https://www.sephora.com.mx';

@Injectable()
export class SephoraScraper {
  private readonly logger = new Logger(SephoraScraper.name);

  constructor(
    private readonly productRepository: ProductRepository,
    private readonly priceValidator: PriceValidationService,
  ) {}

  async scrapeCategory(
    url: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    const term = new URL(url).pathname.split('/').pop() || 'category';
    this.logger.log(`🚀 Starting Sephora scrape for: ${term}`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    const uniqueQueueId = `sephora_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const requestQueue = await RequestQueue.open(uniqueQueueId);

    const router = createCheerioRouter();

    router.addDefaultHandler(
      async ({ request, log, body }: CheerioCrawlingContext) => {
        const currentUrl = request.url;
        const pageParam = new URL(currentUrl).searchParams.get('page') || '1';
        const pageNumber = parseInt(pageParam);

        log.info(`📄 Processing page ${pageNumber}...`);

        try {
          let data: any;
          const bodyStr =
            typeof body === 'string' ? body : (body?.toString('utf-8') ?? '');

          if (bodyStr.startsWith('{') || bodyStr.startsWith('[')) {
            try {
              data = JSON.parse(bodyStr);
            } catch (e) {
              log.warning(`Failed to parse body as JSON: ${e.message}`);
            }
          }

          if (!data) {
            log.warning(`⚠️ No JSON data found on page ${pageNumber}`);
            return;
          }

          const results: any[] = data?.response?.results ?? [];
          const products = this.extractProducts(results);

          if (products.length > 0) {
            log.info(
              `✅ Found ${products.length} products on page ${pageNumber}`,
            );
            const validated = await this.priceValidator.validateBatch(
              products,
              BEAUTY_RULES,
            );
            await this.productRepository.bulkUpsert(validated);
            totalScraped += validated.length;
            allProducts.push(...validated);
            await progress?.onProgress?.(totalScraped);
          } else {
            log.warning(`⚠️ No valid products on page ${pageNumber}`);
          }

          if (pageNumber === 1) {
            const totalResults: number = data?.response?.total_num_results ?? 0;
            const pageSize = parseInt(
              new URL(currentUrl).searchParams.get('num_results_per_page') ??
                '52',
            );
            const totalPages = Math.min(Math.ceil(totalResults / pageSize), 50);

            log.info(`📊 Total results: ${totalResults}, pages: ${totalPages}`);

            for (let p = 2; p <= totalPages; p++) {
              const nextUrl = new URL(currentUrl);
              nextUrl.searchParams.set('page', p.toString());
              nextUrl.searchParams.set('_dt', Date.now().toString());
              await requestQueue.addRequest({ url: nextUrl.toString() });
            }
          }
        } catch (e) {
          log.error(`❌ Error processing page ${pageNumber}: ${e.message}`);
          await progress?.onLog?.(
            `❌ Error on page ${pageNumber}: ${e.message}`,
          );
        }
      },
    );

    const initialUrl = new URL(url);
    initialUrl.searchParams.set('_dt', Date.now().toString());

    const crawler = new CheerioCrawler({
      requestHandler: router,
      requestQueue,
      maxConcurrency: 1,
      requestHandlerTimeoutSecs: 60,
      additionalMimeTypes: ['application/json', 'text/plain'],
    });

    await requestQueue.addRequest({ url: initialUrl.toString() });
    await crawler.run();
    await requestQueue.drop();

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products for "${term}".`,
    );
    return allProducts;
  }

  private extractProducts(results: any[]): ScrapedProduct[] {
    const extracted: ScrapedProduct[] = [];
    for (const result of results) {
      const item = this.parseResult(result);
      if (item) extracted.push(item);
    }
    return extracted;
  }

  private parseResult(result: any): ScrapedProduct | null {
    try {
      const d = result?.data;
      if (!d) return null;

      const name: string = d.masterProductName || result.value;
      const sku: string = String(d.variation_id);
      const url: string = d.url;
      const externalId: string = String(d.id);
      const price: number = Number(d.price) || 0;
      const salePrice: number = Number(d.sale_price) || 0;
      const availability: string = d.availability ?? '';

      if (!name || !sku || !url) return null;
      if (price <= 0 || salePrice <= 0) return null;
      if (availability !== 'in stock') return null;

      const imageRaw: string = d.image_url ?? '';
      const image = imageRaw.startsWith('http')
        ? imageRaw
        : `${SEPHORA_BASE_URL}${imageRaw}`;

      return {
        name,
        sku,
        url,
        current_price: salePrice,
        original_price: price,
        source: 'sephora',
        image: imageRaw ? image : undefined,
        external_id: externalId,
      };
    } catch {
      return null;
    }
  }
}
