import { Injectable, Logger, OnModuleDestroy } from '@nestjs/common';
import Redis from 'ioredis';
import axios from 'axios';

/**
 * Lightweight system-health monitor for the TypeScript scrapers, mirroring the
 * Python `app/monitoring.py` Monitor. It tracks consecutive failures per source
 * in Redis db=1 under the SAME `monitor:<service>:failures` key format, so the
 * existing FastAPI status view (`app/api.py` -> `get_services_status`) surfaces
 * TS sources alongside the Python ones with no changes on that side.
 *
 * Why this exists: Office Depot moved from the Python celery task to this
 * backend, but its `scan_officedepot_deals` schedule is commented out in celery
 * beat — so the Python `monitor.record_*('officedepot')` calls never fire and
 * NOTHING watched OD. If OD broke entirely, no system alert would go out.
 *
 * Design note — a single flaky category must NOT alert: OD's `04-037-0-0`
 * (desktop computers) gets intermittently tarpitted by the WAF. Because ANY
 * category that returns products calls `recordSuccess`, which resets the
 * counter, the failure count only climbs when OD fails as a WHOLE. That keeps
 * the alert quiet on known single-category flakiness and loud on real outages.
 */
@Injectable()
export class MonitorService implements OnModuleDestroy {
    private readonly logger = new Logger(MonitorService.name);
    private readonly redis: Redis;
    private readonly telegramToken = process.env.TELEGRAM_TOKEN;
    private readonly alertsChatId = process.env.TELEGRAM_ALERTS_CHAT_ID;

    // Consecutive-failure thresholds per service. A full OD pass dispatches ~7
    // categories, so 6 failures in a row ≈ the whole store is down rather than
    // one flaky category.
    private readonly THRESHOLDS: Record<string, number> = {
        officedepot: 6,
    };

    constructor() {
        const url = process.env.REDIS_URL || 'redis://redis:6379/0';
        // Force db=1 to share keys with the Python monitor (app/monitoring.py).
        const db1Url = /\/\d+$/.test(url)
            ? url.replace(/\/\d+$/, '/1')
            : `${url.replace(/\/$/, '')}/1`;
        this.redis = new Redis(db1Url, { maxRetriesPerRequest: null });
        this.redis.on('error', (e) =>
            this.logger.error(`Monitor Redis error: ${e.message}`),
        );
    }

    async onModuleDestroy() {
        try {
            await this.redis.quit();
        } catch {
            /* noop */
        }
    }

    private key(service: string) {
        return `monitor:${service}:failures`;
    }

    /** A scrape run produced products — clear the failure counter. */
    async recordSuccess(service: string) {
        try {
            const k = this.key(service);
            const prev = parseInt((await this.redis.get(k)) || '0', 10);
            if (prev > 0) {
                this.logger.log(
                    `✅ ${service} recovered after ${prev} consecutive failure(s).`,
                );
            }
            await this.redis.del(k);
        } catch (e) {
            this.logger.error(`recordSuccess(${service}) failed: ${e.message}`);
        }
    }

    /** A scrape run failed — it threw, or returned zero products. */
    async recordFailure(service: string, reason: string) {
        try {
            const k = this.key(service);
            const count = await this.redis.incr(k);
            const limit = this.THRESHOLDS[service] ?? 6;
            this.logger.warn(`⚠️ ${service} failure #${count}/${limit}: ${reason}`);

            if (count === limit) {
                await this.sendSystemAlert(
                    `Fallas repetidas en ${service}`,
                    `El scraper ha devuelto 0 productos ${count} veces consecutivas.\n` +
                        `Posible cambio de layout, bloqueo WAF o IP baneada.\n` +
                        `Último motivo: ${reason}`,
                );
            } else if (count > limit && (count - limit) % 20 === 0) {
                await this.sendSystemAlert(
                    `Persisten fallas en ${service}`,
                    `El scraper lleva ${count} corridas consecutivas fallando. Revisar logs de backend-ts.`,
                );
            }
        } catch (e) {
            this.logger.error(`recordFailure(${service}) failed: ${e.message}`);
        }
    }

    private async sendSystemAlert(title: string, message: string) {
        if (!this.telegramToken || !this.alertsChatId) {
            this.logger.warn(
                '⚠️ TELEGRAM_TOKEN or TELEGRAM_ALERTS_CHAT_ID not set — system alert suppressed.',
            );
            return;
        }
        const text =
            `⚠️ SYSTEM ALERT ⚠️\n\n${title}\n${message}\n\n` +
            `🕒 ${new Date().toLocaleString('es-MX', { timeZone: 'America/Mexico_City' })}`;
        try {
            await axios.post(
                `https://api.telegram.org/bot${this.telegramToken}/sendMessage`,
                { chat_id: this.alertsChatId, text },
            );
            this.logger.log(`✅ System alert sent: ${title}`);
        } catch (e) {
            this.logger.error(`Failed to send system alert: ${e.message}`);
        }
    }
}
