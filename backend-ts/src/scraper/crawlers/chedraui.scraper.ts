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
export class ChedrauiScraper {
  private readonly logger = new Logger(ChedrauiScraper.name);

  // VTEX catalog API returns at most 50 items per request (_to - _from <= 49)
  // and caps the offset window; requests past ~2500 return HTTP 416.
  private static readonly PAGE_SIZE = 50;
  private static readonly MAX_OFFSET = 2450;

  constructor(
    private readonly productRepository: ProductRepository,
    private readonly priceValidator: PriceValidationService,
  ) {}

  async scrapeCategory(
    url: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    const categoryLabel = this.categoryFromUrl(url);
    this.logger.log(`🚀 Starting Chedraui scrape for: ${categoryLabel}`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    const uniqueQueueId = `chedraui_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const requestQueue = await RequestQueue.open(uniqueQueueId);

    const router = createCheerioRouter();

    router.addDefaultHandler(
      async ({ request, log, json, body }: CheerioCrawlingContext) => {
        const currentUrl = request.url;
        const from = parseInt(
          new URL(currentUrl).searchParams.get('_from') || '0',
        );
        const pageInfo = `offset ${from}`;

        log.info(`📄 Processing ${pageInfo}...`);

        try {
          let data: any = json;
          if (!data && typeof body === 'string' && body.trim().startsWith('[')) {
            try {
              data = JSON.parse(body);
            } catch (e) {
              log.warning(`Failed to parse body as JSON: ${e.message}`);
            }
          }

          if (!Array.isArray(data)) {
            log.warning(`⚠️ No JSON array on ${currentUrl}`);
            return;
          }

          const rawCount = data.length;
          const products = this.extractProducts(data);

          if (products.length > 0) {
            log.info(`✅ Found ${products.length} products on ${pageInfo}`);
            const validated = await this.priceValidator.validateBatch(
              products,
              ELECTRONICS_RULES,
            );
            await this.productRepository.bulkUpsert(validated);
            totalScraped += validated.length;
            allProducts.push(...validated);
            await progress?.onProgress?.(totalScraped);
          }

          // Enqueue next page only from the first request (offset 0), stopping
          // when a full page was returned (a short page means the catalog ended).
          if (
            from === 0 &&
            rawCount === ChedrauiScraper.PAGE_SIZE
          ) {
            for (
              let offset = ChedrauiScraper.PAGE_SIZE;
              offset <= ChedrauiScraper.MAX_OFFSET;
              offset += ChedrauiScraper.PAGE_SIZE
            ) {
              const nextUrl = new URL(currentUrl);
              nextUrl.searchParams.set('_from', offset.toString());
              nextUrl.searchParams.set(
                '_to',
                (offset + ChedrauiScraper.PAGE_SIZE - 1).toString(),
              );
              await requestQueue.addRequest({ url: nextUrl.toString() });
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
      maxConcurrency: 1,
      requestHandlerTimeoutSecs: 60,
      // VTEX returns HTTP 206 (partial content) for paged catalog responses,
      // which Crawlee treats as a success (only >=500 / explicit 4xx are errors).
      additionalMimeTypes: ['application/json', 'text/plain'],
    });

    await requestQueue.addRequest({ url });
    await crawler.run();
    await requestQueue.drop();

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products total for ${categoryLabel}.`,
    );
    return allProducts;
  }

  private categoryFromUrl(url: string): string {
    const m = url.match(/products\/search\/([^?]+)/);
    return m ? decodeURIComponent(m[1]) : 'category';
  }

  private extractProducts(data: any[]): ScrapedProduct[] {
    const extracted: ScrapedProduct[] = [];
    for (const p of data) {
      const item = this.parseSingleProduct(p);
      if (item) extracted.push(item);
    }
    return extracted;
  }

  private parseSingleProduct(p: any): ScrapedProduct | null {
    try {
      const item = p?.items?.[0];
      if (!item) return null;

      // Prefer the default seller, else the first with a commercial offer.
      const seller =
        item.sellers?.find((s: any) => s.sellerDefault) ||
        item.sellers?.find((s: any) => s.commertialOffer) ||
        item.sellers?.[0];
      const offer = seller?.commertialOffer;
      if (!offer) return null;

      if (offer.IsAvailable === false) return null;
      if (typeof offer.AvailableQuantity === 'number' && offer.AvailableQuantity <= 0) {
        return null;
      }

      const currentPrice = Number(offer.Price) || 0;
      const listPrice = Number(offer.ListPrice) || 0;
      const priceNoDiscount = Number(offer.PriceWithoutDiscount) || 0;
      if (currentPrice <= 0) return null;

      const originalPrice = Math.max(currentPrice, listPrice, priceNoDiscount);

      const name = p.productName || item.nameComplete || item.name;
      const productUrl = p.link;
      if (!name || !productUrl) return null;

      const image =
        item.images?.[0]?.imageUrl ||
        item.images?.[0]?.imageUrlXL ||
        undefined;

      return {
        name,
        sku: `chedraui-${item.itemId}`,
        url: productUrl,
        current_price: currentPrice,
        original_price: originalPrice,
        source: 'chedraui',
        image: typeof image === 'string' ? image : undefined,
        external_id: String(item.itemId),
      };
    } catch {
      return null;
    }
  }
}
