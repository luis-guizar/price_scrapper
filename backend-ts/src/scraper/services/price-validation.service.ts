import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../../prisma.service';
import { ScrapedProduct } from '../repositories/product.repository';
import {
    PriceGuardRule,
    capUnreasonableOriginalPrice,
} from '../utils/price-guard';

interface HistoricalRow {
    sku: string | null;
    original_price: number | null;
    current_price: number | null;
    price_history: { price: number | null }[];
}

@Injectable()
export class PriceValidationService {
    private readonly logger = new Logger(PriceValidationService.name);

    // Layer 1: reject incoming original_price > anchor × this multiplier
    private static readonly SURGE_THRESHOLD = 1.4;
    // Layer 2: reject incoming original_price > current_price × this multiplier
    private static readonly MAX_ORIGINAL_RATIO = 2.5;
    // Layer 1: how many recent price_history rows to consider for the median
    private static readonly HISTORY_WINDOW = 10;
    // Layer 1: minimum history rows before the median is trusted as the anchor
    private static readonly HISTORY_MIN_TRUST = 3;

    constructor(private prisma: PrismaService) {}

    /**
     * Validate a batch of scraped products against three layers:
     *   1. Historical DB anchor (median of recent price_history)
     *   2. New-product ratio check
     *   3. Static keyword ceiling
     *
     * Uses a single Prisma round-trip to fetch all historical context, then
     * applies the pipeline per product in memory.
     */
    async validateBatch(
        products: ScrapedProduct[],
        rules: PriceGuardRule[],
    ): Promise<ScrapedProduct[]> {
        if (products.length === 0) return products;

        const skus = products.map(p => p.sku).filter((s): s is string => Boolean(s));

        const historicalRows = skus.length === 0 ? [] : await this.prisma.products.findMany({
            where: { sku: { in: skus } },
            select: {
                sku: true,
                original_price: true,
                current_price: true,
                price_history: {
                    select: { price: true },
                    orderBy: { timestamp: 'desc' },
                    take: PriceValidationService.HISTORY_WINDOW,
                },
            },
        });

        const anchors = new Map<string, HistoricalRow>();
        for (const row of historicalRows) {
            if (row.sku) anchors.set(row.sku, row as HistoricalRow);
        }

        return products.map(p => this.applyPipeline(p, anchors.get(p.sku) ?? null, rules));
    }

    /**
     * Median is robust to a single bad scrape — one poisoned row cannot shift
     * the anchor enough to lock in a wrong value. Falls back to stored fields
     * when history is too thin to trust.
     */
    private deriveAnchor(row: HistoricalRow): number | null {
        const history = row.price_history
            .map(h => h.price)
            .filter((n): n is number => typeof n === 'number' && n > 0);

        if (history.length >= PriceValidationService.HISTORY_MIN_TRUST) {
            const sorted = [...history].sort((a, b) => a - b);
            const mid = Math.floor(sorted.length / 2);
            return sorted.length % 2
                ? sorted[mid]
                : (sorted[mid - 1] + sorted[mid]) / 2;
        }

        return row.original_price ?? row.current_price ?? null;
    }

    private applyPipeline(
        p: ScrapedProduct,
        row: HistoricalRow | null,
        rules: PriceGuardRule[],
    ): ScrapedProduct {
        let validated = p.original_price;

        if (row) {
            // === LAYER 1: HISTORICAL ANCHOR ===
            const anchor = this.deriveAnchor(row);
            if (
                anchor !== null &&
                anchor > 0 &&
                p.original_price > anchor * PriceValidationService.SURGE_THRESHOLD
            ) {
                this.logger.warn(
                    `[Anchor] ${p.source}/${p.sku} surge rejected: ${p.original_price} → ${anchor}`,
                );
                validated = anchor;
            }
        } else {
            // === LAYER 2: NEW-PRODUCT RATIO CHECK ===
            // Suspected structural decimal/scraping error: clamp to current_price.
            if (
                p.current_price > 0 &&
                p.original_price > p.current_price * PriceValidationService.MAX_ORIGINAL_RATIO
            ) {
                this.logger.warn(
                    `[Ratio] ${p.source}/${p.sku} ${p.original_price} > 2.5×${p.current_price}, clamping`,
                );
                validated = p.current_price;
            }
        }

        // === LAYER 3: STATIC KEYWORD CEILING (absolute safety net) ===
        validated = capUnreasonableOriginalPrice(
            p.name,
            p.current_price,
            validated,
            rules,
            (t, from, to) => {
                this.logger.warn(`[Ceiling] ${p.source} "${t}": ${from} → ${to}`);
            },
        );

        return { ...p, original_price: validated };
    }
}
