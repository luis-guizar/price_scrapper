import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { PrismaService } from './prisma.service';
import axios from 'axios';

@Injectable()
export class TelegramListenerService implements OnModuleInit {
    private readonly logger = new Logger(TelegramListenerService.name);
    private readonly telegramToken = process.env.TELEGRAM_TOKEN;
    private lastUpdateId = 0;

    constructor(private prisma: PrismaService) { }

    async onModuleInit() {
        if (!this.telegramToken) return;
        // Defensive: getUpdates 409s if a webhook is configured on this bot.
        try {
            await axios.post(`https://api.telegram.org/bot${this.telegramToken}/deleteWebhook`);
        } catch (e) {
            this.logger.warn(`Could not clear Telegram webhook: ${e.message}`);
        }
    }

    // Poll for replies to alert messages so users can disable alerts by replying "stop" etc.
    @Cron('*/10 * * * * *')
    async pollTelegramUpdates() {
        if (!this.telegramToken) return;

        try {
            const res = await axios.get(`https://api.telegram.org/bot${this.telegramToken}/getUpdates`, {
                params: {
                    offset: this.lastUpdateId + 1,
                    timeout: 0,
                    allowed_updates: JSON.stringify(['message']),
                },
            });

            for (const update of res.data.result || []) {
                this.lastUpdateId = update.update_id;
                await this.handleUpdate(update);
            }
        } catch (e) {
            this.logger.error(`Failed polling Telegram updates: ${e.message}`);
        }
    }

    private async handleUpdate(update: any) {
        const message = update.message;
        const replyTo = message?.reply_to_message;
        if (!replyTo) return;

        const alert = await this.prisma.alerts.findFirst({
            where: {
                telegram_message_id: replyTo.message_id,
                telegram_chat_id: BigInt(message.chat.id),
            },
        });
        if (!alert?.product_id) return;

        const product = await this.prisma.products.findUnique({ where: { id: alert.product_id } });
        if (!product || !product.is_active) return; // already muted, or gone

        await this.prisma.products.update({ where: { id: product.id }, data: { is_active: false } });
        this.logger.log(`🔕 Disabled alerts for "${product.name}" via Telegram reply`);

        try {
            await axios.post(`https://api.telegram.org/bot${this.telegramToken}/sendMessage`, {
                chat_id: message.chat.id,
                text: `🔕 Alertas desactivadas para: ${product.name}`,
                reply_to_message_id: message.message_id,
            });
        } catch (e) {
            this.logger.error(`Failed to send confirmation reply: ${e.message}`);
        }
    }
}
