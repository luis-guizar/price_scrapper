import { Injectable, Logger } from '@nestjs/common';
import axios from 'axios';
import {
  ProductRepository,
  ScrapedProduct,
} from '../repositories/product.repository';
import { ScrapeProgress } from '../scraper.types';
import { ELECTRONICS_RULES } from '../utils/price-guard';
import { PriceValidationService } from '../services/price-validation.service';
import { SEARS_CONFIG } from '../constants';

@Injectable()
export class SearsScraper {
  private readonly logger = new Logger(SearsScraper.name);

  private static readonly HITS_PER_PAGE = 100;
  private static readonly MAX_PAGES = 15;

  constructor(
    private readonly productRepository: ProductRepository,
    private readonly priceValidator: PriceValidationService,
  ) {}

  /**
   * Sears is scraped through its public Algolia search index. The `term`
   * argument is a plain search keyword (from SEARS_CONFIG.urls); we POST it to
   * Algolia and page through the results (0-indexed pages).
   */
  async scrapeCategory(
    term: string,
    progress?: ScrapeProgress,
  ): Promise<ScrapedProduct[]> {
    this.logger.log(`🚀 Starting Sears scrape for: "${term}"`);
    let totalScraped = 0;
    const allProducts: ScrapedProduct[] = [];

    const { appId, apiKey, index } = SEARS_CONFIG.algolia;
    const endpoint = `https://${appId}-dsn.algolia.net/1/indexes/${index}/query`;

    let page = 0;
    let nbPages = 1;

    try {
      do {
        const res = await axios.post(
          endpoint,
          { query: term, hitsPerPage: SearsScraper.HITS_PER_PAGE, page },
          {
            headers: {
              'X-Algolia-Application-Id': appId,
              'X-Algolia-API-Key': apiKey,
              'Content-Type': 'application/json',
            },
            timeout: 30_000,
          },
        );

        const data = res.data || {};
        const hits: any[] = Array.isArray(data.hits) ? data.hits : [];
        if (page === 0) {
          nbPages = Math.min(Number(data.nbPages) || 1, SearsScraper.MAX_PAGES);
          this.logger.log(
            `📊 "${term}": ${data.nbHits ?? '?'} hits across ${nbPages} page(s)`,
          );
        }

        const products = this.extractProducts(hits);
        if (products.length > 0) {
          const validated = await this.priceValidator.validateBatch(
            products,
            ELECTRONICS_RULES,
          );
          await this.productRepository.bulkUpsert(validated);
          totalScraped += validated.length;
          allProducts.push(...validated);
          await progress?.onProgress?.(totalScraped);
        }

        page += 1;
      } while (page < nbPages);
    } catch (e: any) {
      this.logger.error(`❌ Error scraping Sears "${term}": ${e.message}`);
      await progress?.onLog?.(`❌ Error on "${term}": ${e.message}`);
    }

    this.logger.log(
      `✅ Finished: Scraped ${totalScraped} products total for "${term}".`,
    );
    return allProducts;
  }

  private extractProducts(hits: any[]): ScrapedProduct[] {
    const extracted: ScrapedProduct[] = [];
    for (const h of hits) {
      const item = this.parseHit(h);
      if (item) extracted.push(item);
    }
    return extracted;
  }

  private parseHit(h: any): ScrapedProduct | null {
    try {
      if (h.is_active === false) return null;
      if (typeof h.stock === 'number' && h.stock <= 0) return null;

      const name: string = h.title;
      const id: string = String(h.objectID ?? h.sku ?? '');
      if (!name || !id) return null;

      const salePrice = Number(h.sale_price) || 0;
      const price = Number(h.price) || 0;
      const currentPrice = salePrice > 0 ? salePrice : price;
      if (currentPrice <= 0) return null;
      const originalPrice = Math.max(currentPrice, price);

      const slug = this.slugify(name);
      const url = `${SEARS_CONFIG.baseUrl}/producto/${id}/${slug}`;

      const photo = Array.isArray(h.photos) ? h.photos[0] : undefined;
      const image = photo?.source || photo?.thumbnail || undefined;

      return {
        name,
        sku: `sears-${id}`,
        url,
        current_price: currentPrice,
        original_price: originalPrice,
        source: 'sears',
        image: typeof image === 'string' ? image : undefined,
        external_id: id,
      };
    } catch {
      return null;
    }
  }

  private slugify(text: string): string {
    // Cosmetic only — Sears routes by the numeric product id, so a stripped
    // ASCII slug is sufficient (accented chars collapse into separators).
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '')
      .slice(0, 80);
  }
}
