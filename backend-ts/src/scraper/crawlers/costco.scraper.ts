import { Injectable, Logger } from '@nestjs/common';
import axios from 'axios';
import {
  ProductRepository,
  ScrapedProduct,
} from '../repositories/product.repository';
import { ScrapeProgress } from '../scraper.types';
import { ELECTRONICS_RULES } from '../utils/price-guard';
import { PriceValidationService } from '../services/price-validation.service';
import { COSTCO_CONFIG } from '../constants';

@Injectable()
export class CostcoScraper {
  private readonly logger = new Logger(CostcoScraper.name);

  private static readonly PAGE_SIZE = 100;
  private static readonly MAX_PAGES = 10;
  private static readonly OCC_BASE =
    'https://www.costco.com.mx/rest/v2/mexico/products/search';

  private readonly userAgent =
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

  constructor(
    private readonly productRepository: ProductRepository,
    private readonly priceValidator: PriceValidationService,
  ) {}

  /**
   * Costco is scraped through its Spartacus OCC search API. The `term` argument
   * is a plain keyword (from COSTCO_CONFIG.urls); we page through OCC results.
   * The search payload has no MSRP, so `original_price` is seeded to the current
   * price and real drops are detected via accumulated price_history.
   */
  async scrapeCategory(
    term: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    this.logger.log(`🚀 Starting Costco scrape for: "${term}"`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    let currentPage = 0;
    let totalPages = 1;

    try {
      do {
        const res = await axios.get(CostcoScraper.OCC_BASE, {
          params: {
            fields: 'FULL',
            query: term,
            pageSize: CostcoScraper.PAGE_SIZE,
            currentPage,
            lang: 'es_MX',
            curr: 'MXN',
          },
          headers: {
            Accept: 'application/json',
            'User-Agent': this.userAgent,
            'Accept-Language': 'es-MX,es;q=0.9',
          },
          timeout: 30_000,
        });

        const data = res.data || {};
        const products: any[] = Array.isArray(data.products)
          ? data.products
          : [];
        if (currentPage === 0) {
          totalPages = Math.min(
            Number(data.pagination?.totalPages) || 1,
            CostcoScraper.MAX_PAGES,
          );
          this.logger.log(
            `📊 "${term}": ${data.pagination?.totalResults ?? '?'} results across ${totalPages} page(s)`,
          );
        }

        const parsed = this.extractProducts(products);
        if (parsed.length > 0) {
          const validated = await this.priceValidator.validateBatch(
            parsed,
            ELECTRONICS_RULES,
          );
          await this.productRepository.bulkUpsert(validated);
          totalScraped += validated.length;
          allProducts.push(...validated);
          await progress?.onProgress?.(totalScraped);
        }

        currentPage += 1;
      } while (currentPage < totalPages);
    } catch (e: any) {
      this.logger.error(`❌ Error scraping Costco "${term}": ${e.message}`);
      await progress?.onLog?.(`❌ Error on "${term}": ${e.message}`);
    }

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products total for "${term}".`,
    );
    return allProducts;
  }

  private extractProducts(products: any[]): ScrapedProduct[] {
    const extracted: ScrapedProduct[] = [];
    for (const p of products) {
      const item = this.parseProduct(p);
      if (item) extracted.push(item);
    }
    return extracted;
  }

  private parseProduct(p: any): ScrapedProduct | null {
    try {
      const stockStatus = p.stock?.stockLevelStatus;
      if (stockStatus && stockStatus !== 'inStock') return null;

      const name: string = p.name;
      const code: string = String(p.code ?? '');
      if (!name || !code) return null;

      const currentPrice = Number(p.price?.value) || 0;
      if (currentPrice <= 0) return null;
      // No MSRP in the search response; seed original to current price.
      const originalPrice = Math.max(
        currentPrice,
        Number(p.basePrice?.value) || 0,
      );

      const rawUrl: string = p.url || '';
      const url = rawUrl.startsWith('http')
        ? rawUrl
        : `${COSTCO_CONFIG.baseUrl}${rawUrl}`;
      if (!rawUrl) return null;

      const rawImg = p.images?.find((i: any) => i.url)?.url;
      const image = rawImg
        ? rawImg.startsWith('http')
          ? rawImg
          : `${COSTCO_CONFIG.baseUrl}${rawImg}`
        : undefined;

      return {
        name,
        sku: `costco-${code}`,
        url,
        current_price: currentPrice,
        original_price: originalPrice,
        source: 'costco',
        image,
        external_id: code,
      };
    } catch {
      return null;
    }
  }
}
