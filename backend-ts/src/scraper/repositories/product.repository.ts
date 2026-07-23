import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../../prisma.service';
import { Prisma } from '@prisma/client';

export interface ScrapedProduct {
    name: string;
    url: string;
    sku: string;
    current_price: number;
    original_price: number;
    source: string;
    image?: string;
    external_id?: string;
}

/**
 * How the `original_price` alert anchor is maintained on upsert.
 * - 'overwrite' (default): anchor tracks the latest scraped original_price.
 *   Correct for sources that carry a real MSRP/list price (Costco basePrice,
 *   Sears/Liverpool list price).
 * - 'max': anchor is the highest price ever seen. Used by Office Depot, whose
 *   feed exposes only a single `price` (original_price === current_price), so
 *   'overwrite' would collapse the anchor to the current price and make the
 *   ≥50%-off rule impossible to satisfy. Running-max gives OD a "regular price"
 *   proxy so genuine drops from its own high can alert.
 */
export type AnchorStrategy = 'overwrite' | 'max';

@Injectable()
export class ProductRepository {
    private readonly logger = new Logger(ProductRepository.name);

    constructor(private prisma: PrismaService) { }

    async bulkUpsert(products: ScrapedProduct[], anchorStrategy: AnchorStrategy = 'overwrite') {
        if (products.length === 0) return;

        // Deduplicate products by SKU to prevent conflicts in the same batch
        const uniqueProductsMap = new Map<string, ScrapedProduct>();
        for (const p of products) {
            uniqueProductsMap.set(p.sku, p);
        }
        const uniqueProducts = Array.from(uniqueProductsMap.values());

        const values: string[] = [];
        const params: any[] = [];

        uniqueProducts.forEach((p, index) => {
            // Parameters for: name, url, sku, current_price, original_price, source, last_checked, external_id
            const offset = index * 8;
            values.push(`($${offset + 1}, $${offset + 2}, $${offset + 3}, $${offset + 4}, $${offset + 5}, $${offset + 6}, $${offset + 7}, $${offset + 8})`);

            params.push(
                p.name,
                p.url,
                p.sku,
                p.current_price,
                p.original_price,
                p.source,
                new Date(), // $7: last_checked
                p.external_id || null // $8: external_id
            );
        });

        // GREATEST ignores NULLs in Postgres, so a NULL existing anchor still
        // resolves to the new value on the first 'max' upsert.
        const anchorAssignment =
            anchorStrategy === 'max'
                ? 'original_price = GREATEST(products.original_price, EXCLUDED.original_price)'
                : 'original_price = EXCLUDED.original_price';

        const query = `
      INSERT INTO products (name, url, sku, current_price, original_price, source, last_checked, external_id)
      VALUES ${values.join(', ')}
      ON CONFLICT (sku) DO UPDATE SET
        current_price = EXCLUDED.current_price,
        ${anchorAssignment},
        last_checked = NOW(),
        name = EXCLUDED.name
    `;

        try {
            const startTime = Date.now();
            await this.prisma.$executeRawUnsafe(query, ...params);
            const elapsed = Date.now() - startTime;
            this.logger.log(`💾 Scored ${uniqueProducts.length} products to database (${elapsed}ms)`);
        } catch (error) {
            this.logger.error(`❌ Error in bulkUpsert: ${error}`);
            throw error;
        }
    }
}
