import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from './prisma.service';
import { ScrapedProduct } from './scraper/repositories/product.repository';
import axios from 'axios';

@Injectable()
export class AlertService {
    private readonly logger = new Logger(AlertService.name);
    private readonly telegramToken = process.env.TELEGRAM_TOKEN;
    private readonly telegramChatId = process.env.TELEGRAM_CHAT_ID;
    private readonly telegramHighPriorityChatId = process.env.TELEGRAM_HIGH_PRIORITY_CHAT_ID;
    private readonly dashboardBaseUrl = process.env.DASHBOARD_BASE_URL;

    // Minimum drop vs the product's OWN recent price history (a genuine event).
    // Measured against a trailing baseline, NOT the retailer's self-reported
    // "antes"/MSRP anchor — that anchor is frequently a permanent fiction
    // (e.g. Sears appliances list a ~2x inflated original_price forever).
    private readonly REAL_DROP_PCT = parseInt(process.env.ALERT_REAL_DROP_PCT || '30');
    // How many recent price_history rows to pull to build the trailing baseline.
    private readonly HISTORY_WINDOW = 8;
    private readonly HIGH_PRIORITY_PCT = 30; // genuine drop % that routes to the priority chat
    private readonly MAX_ALERTS_PER_BATCH = 10;

    private median(values: number[]): number {
        const sorted = [...values].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 !== 0
            ? sorted[mid]
            : (sorted[mid - 1] + sorted[mid]) / 2;
    }

    constructor(
        private prisma: PrismaService,
    ) { }

    /**
     * Checks a batch of scraped products for meaningful price drops.
     * Uses history to confirm a real-time DROP occurred (prevents discovery spam).
     */
    async checkAndSendAlerts(products: ScrapedProduct[]) {
        if (!this.telegramToken || !this.telegramChatId) {
            this.logger.warn('⚠️ TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not configured. Alerts disabled.');
            return;
        }

        const sourceName = products[0]?.source || 'unknown';
        this.logger.log(`📊 Processing ${products.length} products for ${sourceName} alerts...`);

        let sentCount = 0;
        let checkedCount = 0;

        for (const product of products) {
            if (sentCount >= this.MAX_ALERTS_PER_BATCH) {
                this.logger.warn(`✋ Reached MAX_ALERTS_PER_BATCH (${this.MAX_ALERTS_PER_BATCH}) for this run. Skipping further alerts.`);
                break;
            }

            try {
                checkedCount++;
                if (!product.current_price || product.current_price <= 0) continue;

                // 2. Fetch anchor and history info
                const dbProduct = await this.prisma.products.findUnique({
                    where: { url: product.url },
                    include: {
                        price_history: {
                            orderBy: { timestamp: 'desc' },
                            take: this.HISTORY_WINDOW // Current + trailing window for baseline
                        }
                    }
                });

                if (!dbProduct) continue;

                // Skip if product is not active (unsubscribed) — catches both false and null
                if (!dbProduct.is_active) {
                    this.logger.debug(`🔕 Skipping alert for ${product.name} - Product is inactive (unsubscribed).`);
                    continue;
                }

                // Relevance is judged against the product's OWN recent price
                // history, not against original_price. The retailer's anchor is
                // an unreliable "antes" that is often permanently inflated, which
                // made every everyday price look like a 50%+ deal.
                const history = dbProduct.price_history;

                const currentPrice = product.current_price;
                // history[0] is the freshly-recorded current tick; the rest is the
                // trailing baseline window (previous checks).
                const priorPrices = history
                    .slice(1)
                    .map(h => h.price)
                    .filter((p): p is number => typeof p === 'number' && p > 0);

                // Require at least 2 prior observations (discovery-spam prevention
                // + enough signal for a meaningful baseline).
                if (priorPrices.length < 2) continue;

                const previousPrice = priorPrices[0];        // most recent prior check
                const baseline = this.median(priorPrices);    // robust trailing reference
                const recentLow = Math.min(...priorPrices);

                const genuineDropPct = baseline > 0
                    ? ((baseline - currentPrice) / baseline) * 100
                    : 0;

                // A relevant alert = a genuine, fresh low: the price dropped this
                // tick, is at/below its own recent low (not a bounce), and is
                // meaningfully below the trailing baseline.
                const isRealDeal =
                    currentPrice < previousPrice &&
                    currentPrice <= recentLow &&
                    genuineDropPct >= this.REAL_DROP_PCT;

                if (isRealDeal) {
                    // Deduplication (24h): only re-alert if at least ~2% cheaper
                    // than any alert already sent in the window (kills flat-price
                    // re-spam where the price barely flickers day to day).
                    const alreadyAlerted = await this.prisma.alerts.findFirst({
                        where: {
                            product_id: dbProduct.id,
                            price: { lte: currentPrice * 1.02 },
                            created_at: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) }
                        }
                    });

                    if (!alreadyAlerted) {
                        this.logger.log(`🔔 Sending alert for ${product.name} (${Math.round(genuineDropPct)}% below baseline $${Math.round(baseline)} -> $${currentPrice})`);
                        const sent = await this.sendTelegram(product, genuineDropPct, baseline, dbProduct.id);
                        await this.saveAlertToDb(product, genuineDropPct, baseline, dbProduct.id, sent?.messageId, sent?.chatId);
                        sentCount++;
                        await new Promise(r => setTimeout(r, 1200));
                    } else {
                        this.logger.debug(`✋ ${product.name}: Already alerted recently - skipping`);
                    }
                }
            } catch (e) {
                this.logger.error(`❌ Error in alert check for ${product.name}: ${e.message}`);
            }
        }

        if (sentCount > 0) {
            this.logger.log(`✅ Alert pass complete - ${sentCount} alerts sent, ${checkedCount} checked.`);
        } else {
            this.logger.verbose(`ℹ️ No significant price drops detected among ${checkedCount} products.`);
        }
    }

    private async sendTelegram(product: ScrapedProduct, dropPct: number, referencePrice: number, productId: number): Promise<{ messageId: number, chatId: string } | undefined> {
        // Explicitly filter out 'venta internacional' products
        const titleLower = product.name?.toLowerCase() || '';
        if (titleLower.includes('venta internacional')) {
            this.logger.log(`🚫 Alert blocked: Contiene 'venta internacional' - ${product.name}`);
            return;
        }

        const isHighPriority = dropPct >= this.HIGH_PRIORITY_PCT;
        const prefix = isHighPriority ? '🚨' : '📉';
        // "Antes" is the product's recent trailing price (what it normally sold
        // for lately), not the retailer's inflated MSRP anchor.
        let msg = `${prefix} ¡BAJADA DE PRECIO EN ${product.source.toUpperCase()}! (${Math.round(dropPct)}% OFF)\n\n📦 ${product.name}\n💰 Nuevo Precio: $${product.current_price.toLocaleString()}\n❌ Antes: $${Math.round(referencePrice).toLocaleString()}\n🔗 ${product.url}`;
        if (this.dashboardBaseUrl) {
            msg += `\n🔕 Desactivar: ${this.dashboardBaseUrl}/?product=${productId}`;
        }

        // Route to high-priority chat if available and discount >= 75%
        const targetChatId = (isHighPriority && this.telegramHighPriorityChatId)
            ? this.telegramHighPriorityChatId
            : this.telegramChatId;

        try {
            const res = await axios.post(`https://api.telegram.org/bot${this.telegramToken}/sendMessage`, {
                chat_id: targetChatId,
                text: msg
            });
            if (isHighPriority) {
                this.logger.log(`🚨 HIGH PRIORITY alert sent to priority chat for ${product.name}`);
            }
            return { messageId: res.data?.result?.message_id, chatId: String(targetChatId) };
        } catch (e) {
            this.logger.error(`Failed to send Telegram message: ${e.message}`);
        }
    }

    private async saveAlertToDb(product: ScrapedProduct, dropPct: number, referencePrice: number, productId: number, telegramMessageId?: number, telegramChatId?: string) {
        try {
            await this.prisma.alerts.create({
                data: {
                    product_id: productId,
                    price: product.current_price,
                    previous_price: Math.round(referencePrice),
                    change_pct: Math.round(dropPct),
                    source: product.source,
                    url: product.url,
                    title: product.name,
                    telegram_message_id: telegramMessageId,
                    telegram_chat_id: telegramChatId ? BigInt(telegramChatId) : undefined,
                }
            });
        } catch (e) {
            this.logger.error(`Failed to save alert to DB: ${e.message}`);
        }
    }
}
