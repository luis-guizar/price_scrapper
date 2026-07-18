import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import {
  OFFICE_DEPOT_CONFIG,
  COPPEL_CONFIG,
  LIVERPOOL_CONFIG,
  SEPHORA_CONFIG,
  CHEDRAUI_CONFIG,
  SEARS_CONFIG,
  COSTCO_CONFIG,
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
      await this.scraperQueue.add('scrape:officedepot', { url });
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
      await this.scraperQueue.add('scrape:coppel', { url });
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
      await this.scraperQueue.add('scrape:liverpool', { url });
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
      await this.scraperQueue.add('scrape:sephora', { url });
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Sephora scraping categories.`,
    );
  }

  // Runs every 2 hours (at HH:12 — offset from other stores). Chedraui VTEX
  // catalog API; grocery/electronics/toys.
  @Cron('0 12 */2 * * *')
  async handleChedrauiCron() {
    this.logger.log('🚀 [CRON] Starting automated full-pass for Chedraui...');

    const urls = CHEDRAUI_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add('scrape:chedraui', { url });
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Chedraui scraping categories.`,
    );
  }

  // Runs every hour (at :25). Sears via Algolia search terms.
  @Cron('0 25 * * * *')
  async handleSearsCron() {
    this.logger.log('🚀 [CRON] Starting automated full-pass for Sears...');

    const urls = SEARS_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add('scrape:sears', { url });
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Sears search terms.`,
    );
  }

  // Runs every 2 hours (at HH:48). Costco via Spartacus OCC search terms.
  @Cron('0 48 */2 * * *')
  async handleCostcoCron() {
    this.logger.log('🚀 [CRON] Starting automated full-pass for Costco...');

    const urls = COSTCO_CONFIG.urls;

    for (const url of urls) {
      await this.scraperQueue.add('scrape:costco', { url });
    }

    this.logger.log(
      `✅ [CRON] Dispatched ${urls.length} Costco search terms.`,
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
