import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { OFFICE_DEPOT_CONFIG, COPPEL_CONFIG, LIVERPOOL_CONFIG } from './constants';

@Injectable()
export class ScraperScheduleService {
    private readonly logger = new Logger(ScraperScheduleService.name);

    constructor(@InjectQueue('scraper-tasks') private scraperQueue: Queue) { }

    // Runs every 20 minutes (at :00, :20, :40)
    @Cron('0 0,20,40 * * * *')
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

    // Runs every 20 minutes (at :07, :27, :47 — offset from OD)
    @Cron('0 7,27,47 * * * *')
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

    // Runs every 20 minutes (at :14, :34, :54 — offset from OD & Coppel)
    @Cron('0 14,34,54 * * * *')
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
