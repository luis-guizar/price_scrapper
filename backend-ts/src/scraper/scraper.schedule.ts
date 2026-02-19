import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { OFFICE_DEPOT_CONFIG, COPPEL_CONFIG, LIVERPOOL_CONFIG } from './constants';

@Injectable()
export class ScraperScheduleService {
    private readonly logger = new Logger(ScraperScheduleService.name);

    constructor(@InjectQueue('scraper-tasks') private scraperQueue: Queue) { }

    // Runs every hour at minute 0
    @Cron('0 0 * * * *')
    async handleOfficeDepotCron() {
        this.logger.log('🚀 [CRON] Starting automated full-pass for Office Depot...');

        const urls = OFFICE_DEPOT_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:officedepot', {
                url: url,
            });
        }

        this.logger.log(`✅ [CRON] Dispatched ${urls.length} Office Depot scraping categories.`);
    }

    // Runs every hour at minute 30 (offset to avoid spike with OD)
    @Cron('0 30 * * * *')
    async handleCoppelCron() {
        this.logger.log('🚀 [CRON] Starting automated full-pass for Coppel...');

        const urls = COPPEL_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:coppel', {
                url: url,
            });
        }

        this.logger.log(`✅ [CRON] Dispatched ${urls.length} Coppel scraping categories.`);
    }

    // Runs every hour at minute 15 and 45 (offset to avoid spikes)
    @Cron('0 15,45 * * * *')
    async handleLiverpoolCron() {
        this.logger.log('🚀 [CRON] Starting automated full-pass for Liverpool...');

        const urls = LIVERPOOL_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:liverpool', {
                url: url,
            });
        }

        this.logger.log(`✅ [CRON] Dispatched ${urls.length} Liverpool scraping categories.`);
    }
}
