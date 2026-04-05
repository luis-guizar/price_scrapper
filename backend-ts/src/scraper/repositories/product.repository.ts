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

@Injectable()
export class ProductRepository {
    private readonly logger = new Logger(ProductRepository.name);

    constructor(private prisma: PrismaService) { }

    async bulkUpsert(products: ScrapedProduct[]) {
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

        const query = `
      INSERT INTO products (name, url, sku, current_price, original_price, source, last_checked, external_id)
      VALUES ${values.join(', ')}
      ON CONFLICT (sku) DO UPDATE SET
        current_price = EXCLUDED.current_price,
        last_checked = NOW(),
        name = EXCLUDED.name,
        original_price = COALESCE(products.original_price, EXCLUDED.current_price)
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
