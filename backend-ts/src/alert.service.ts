import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from './prisma.service';
import { ScrapedProduct } from './scraper/repositories/product.repository';
import axios from 'axios';

@Injectable()
export class AlertService {
    private readonly logger = new Logger(AlertService.name);
    private readonly telegramToken = process.env.TELEGRAM_TOKEN;
    private readonly telegramChatId = process.env.TELEGRAM_CHAT_ID;

    // Minimum drop thresholds
    private readonly MIN_DROP_PCT = parseInt(process.env.ALERT_MIN_DISCOUNT_PCT || '40');
    private readonly MIN_DROP_AMOUNT = 6000;
    private readonly MAX_ALERTS_PER_BATCH = 10;

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
                            take: 2 // Current and previous
                        }
                    }
                });

                if (!dbProduct || !dbProduct.original_price) continue;

                // ONLY Alert if we knew this product before (discovery spam prevention)
                const history = dbProduct.price_history;
                if (history.length < 2) continue;

                const currentPrice = product.current_price;
                const previousPrice = history[1].price; // Previous check's price
                const anchorPrice = dbProduct.original_price;

                // Logic: NEW price must be lower than OLD price (a real event happened while we were watching)
                if (currentPrice < (previousPrice || 0)) {
                    const dropMap = anchorPrice - currentPrice;
                    const dropPct = (dropMap / anchorPrice) * 100;

                    if (dropPct >= this.MIN_DROP_PCT || dropMap >= this.MIN_DROP_AMOUNT) {

                        // Check deduplication (24h)
                        const alreadyAlerted = await this.prisma.alerts.findFirst({
                            where: {
                                product_id: dbProduct.id,
                                price: { lte: currentPrice },
                                created_at: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) }
                            }
                        });

                        if (!alreadyAlerted) {
                            this.logger.log(`🔔 Sending alert for ${product.name} (Drop: $${previousPrice} -> $${currentPrice})`);
                            await this.sendTelegram(product, dropPct, anchorPrice);
                            await this.saveAlertToDb(product, dropPct, anchorPrice, dbProduct.id);
                            sentCount++;
                            await new Promise(r => setTimeout(r, 1200));
                        } else {
                            this.logger.debug(`✋ ${product.name}: Already alerted recently - skipping`);
                        }
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

    private async sendTelegram(product: ScrapedProduct, dropPct: number, oldPrice: number) {
        const msg = `📉 ¡BAJADA DE PRECIO EN ${product.source.toUpperCase()}! (${Math.round(dropPct)}% OFF)\n\n📦 ${product.name}\n💰 Nuevo Precio: $${product.current_price.toLocaleString()}\n❌ Antes: $${oldPrice.toLocaleString()}\n🔗 ${product.url}`;

        try {
            await axios.post(`https://api.telegram.org/bot${this.telegramToken}/sendMessage`, {
                chat_id: this.telegramChatId,
                text: msg
            });
        } catch (e) {
            this.logger.error(`Failed to send Telegram message: ${e.message}`);
        }
    }

    private async saveAlertToDb(product: ScrapedProduct, dropPct: number, oldPrice: number, productId: number) {
        try {
            await this.prisma.alerts.create({
                data: {
                    product_id: productId,
                    price: product.current_price,
                    previous_price: oldPrice,
                    change_pct: Math.round(dropPct),
                    source: product.source,
                    url: product.url,
                    title: product.name,
                }
            });
        } catch (e) {
            this.logger.error(`Failed to save alert to DB: ${e.message}`);
        }
    }
}
