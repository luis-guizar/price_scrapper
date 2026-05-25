import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import {
  OFFICE_DEPOT_CONFIG,
  COPPEL_CONFIG,
  LIVERPOOL_CONFIG,
  SEPHORA_CONFIG,
} from './constants';

@Injectable()
export class ScraperScheduleService {
  private readonly logger = new Logger(ScraperScheduleService.name);

  constructor(@InjectQueue('scraper-tasks') private scraperQueue: Queue) {}

  // Runs every 20 minutes (at :00, :20, :40)
  @Cron('0 0,20,40 * * * *')
  async handleOfficeDepotCron() {
    this.logger.log(
      '🚀 [CRON] Starting automated full-pass for Office Depot...',
    );

    const urls = OFFICE_DEPOT_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add(
        'scrape:officedepot',
        { url },
        { jobId: `scrape-officedepot-${url}`.replace(/:/g, '-') },
      );
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Office Depot scraping categories.`,
    );
  }

  // Runs every 2 hours (at HH:07). Reduced from every 20 min: poor deal quality, expensive to run.
  @Cron('0 7 */2 * * *')
  async handleCoppelCron() {
    this.logger.log('🚀 [CRON] Starting automated full-pass for Coppel...');

    const urls = COPPEL_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add(
        'scrape:coppel',
        { url },
        { jobId: `scrape-coppel-${url}`.replace(/:/g, '-') },
      );
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Coppel scraping categories.`,
    );
  }

  // Runs every 20 minutes (at :14, :34, :54 — offset from OD & Coppel)
  @Cron('0 14,34,54 * * * *')
  async handleLiverpoolCron() {
    this.logger.log('🚀 [CRON] Starting automated full-pass for Liverpool...');

    const urls = LIVERPOOL_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add(
        'scrape:liverpool',
        { url },
        { jobId: `scrape-liverpool-${url}`.replace(/:/g, '-') },
      );
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Liverpool scraping categories.`,
    );
  }

  // Runs every 30 minutes (at :03 and :33 — staggered from other stores)
  @Cron('0 3,33 * * * *')
  async handleSephoraCron() {
    this.logger.log('🚀 [CRON] Starting automated full-pass for Sephora...');

    const urls = SEPHORA_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add(
        'scrape:sephora',
        { url },
        { jobId: `scrape-sephora-${url}`.replace(/:/g, '-') },
      );
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Sephora scraping categories.`,
    );
  }

  // Runs every 20 minutes (at :10, :30, :50)
  // @Cron('0 10,30,50 * * * *') // Temporarily disabled due to heavy anti-bot
  handleMeliCron() {
    this.logger.log(
      '⏸️ [CRON] MercadoLibre scraping is temporarily disabled due to anti-bot gating.',
    );

    /*
    const urls = MELI_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add('scrape:meli', {
        url: url,
      });
    }

    this.logger.log(`✅ [CRON] Dispatched ${urls.length} MercadoLibre scraping categories.`);
    */
  }
}
