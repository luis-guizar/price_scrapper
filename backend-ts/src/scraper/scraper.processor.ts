import { Processor, WorkerHost } from '@nestjs/bullmq';
import { Job } from 'bullmq';
import { Logger } from '@nestjs/common';
import { OfficeDepotScraper } from './crawlers/office-depot.scraper';
import { CoppelScraper } from './crawlers/coppel.scraper';
import { LiverpoolScraper } from './crawlers/liverpool.scraper';
import { MeliScraper } from './crawlers/meli.scraper';
import { SephoraScraper } from './crawlers/sephora.scraper';
import { ChedrauiScraper } from './crawlers/chedraui.scraper';
import { SearsScraper } from './crawlers/sears.scraper';
import { CostcoScraper } from './crawlers/costco.scraper';
import { AlertService } from '../alert.service';
import { ScrapeProgress } from './scraper.types';

@Processor('scraper-tasks', { concurrency: 1 })
export class ScraperProcessor extends WorkerHost {
    private readonly logger = new Logger(ScraperProcessor.name);

    constructor(
        private readonly officeDepotScraper: OfficeDepotScraper,
        private readonly coppelScraper: CoppelScraper,
        private readonly liverpoolScraper: LiverpoolScraper,
        private readonly meliScraper: MeliScraper,
        private readonly sephoraScraper: SephoraScraper,
        private readonly chedrauiScraper: ChedrauiScraper,
        private readonly searsScraper: SearsScraper,
        private readonly costcoScraper: CostcoScraper,
        private readonly alertService: AlertService
    ) {
        super();
    }

    async process(job: Job<any, any, string>): Promise<any> {
        const startTime = Date.now();
        const { url } = job.data;
        const categoryLabel = url ? url.split('/').pop()?.substring(0, 20) : 'unknown';

        const progress: ScrapeProgress = {
            onProgress: async (scraped) => { await job.updateProgress({ scraped }); },
            onLog: async (msg) => { await job.log(msg); },
        };

        switch (job.name) {
            case 'scrape:officedepot': {
                this.logger.log(`▶️ [Job ${job.id}] Office Depot: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Office Depot scrape: ${categoryLabel}`);
                const odProducts = await this.officeDepotScraper.scrapeCategory(url, progress);
                if (odProducts && odProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(odProducts);
                }
                const odElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Office Depot: Finished in ${odElapsed}s`);
                await job.log(`Completed: ${odProducts.length} products in ${odElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:coppel': {
                this.logger.log(`▶️ [Job ${job.id}] Coppel: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Coppel scrape: ${categoryLabel}`);
                const products = await this.coppelScraper.scrapeCategory(url, progress);
                if (products && products.length > 0) {
                    await this.alertService.checkAndSendAlerts(products);
                }
                const coppelElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Coppel: Finished in ${coppelElapsed}s`);
                await job.log(`Completed: ${products.length} products in ${coppelElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:liverpool': {
                this.logger.log(`▶️ [Job ${job.id}] Liverpool: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Liverpool scrape: ${categoryLabel}`);
                const liverpoolProducts = await this.liverpoolScraper.scrapeCategory(url, progress);
                if (liverpoolProducts && liverpoolProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(liverpoolProducts);
                }
                const liverpoolElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Liverpool: Finished in ${liverpoolElapsed}s`);
                await job.log(`Completed: ${liverpoolProducts.length} products in ${liverpoolElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:meli': {
                this.logger.log(`▶️ [Job ${job.id}] MercadoLibre: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting MercadoLibre scrape: ${categoryLabel}`);
                const meliProducts = await this.meliScraper.scrapeCategory(url, progress);
                if (meliProducts && meliProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(meliProducts);
                }
                const meliElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] MercadoLibre: Finished in ${meliElapsed}s`);
                await job.log(`Completed: ${meliProducts.length} products in ${meliElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:sephora': {
                this.logger.log(`▶️ [Job ${job.id}] Sephora: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Sephora scrape: ${categoryLabel}`);
                const sephoraProducts = await this.sephoraScraper.scrapeCategory(url, progress);
                // Sephora is intentionally NOT run through checkAndSendAlerts: the
                // electronics-tuned alert rules (≥50% off the original_price anchor,
                // which the beauty price-validator clamps) never fire for it. Sephora
                // deals are surfaced via the dedicated Sephora view instead, which ranks
                // products by discount vs their own historical prices.
                const sephoraElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Sephora: Finished in ${sephoraElapsed}s`);
                await job.log(`Completed: ${sephoraProducts.length} products in ${sephoraElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:chedraui': {
                this.logger.log(`▶️ [Job ${job.id}] Chedraui: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Chedraui scrape: ${categoryLabel}`);
                const chedrauiProducts = await this.chedrauiScraper.scrapeCategory(url, progress);
                if (chedrauiProducts && chedrauiProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(chedrauiProducts);
                }
                const chedrauiElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Chedraui: Finished in ${chedrauiElapsed}s`);
                await job.log(`Completed: ${chedrauiProducts.length} products in ${chedrauiElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:sears': {
                this.logger.log(`▶️ [Job ${job.id}] Sears: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Sears scrape: ${categoryLabel}`);
                const searsProducts = await this.searsScraper.scrapeCategory(url, progress);
                if (searsProducts && searsProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(searsProducts);
                }
                const searsElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Sears: Finished in ${searsElapsed}s`);
                await job.log(`Completed: ${searsProducts.length} products in ${searsElapsed}s`);
                return { status: 'completed' };
            }

            case 'scrape:costco': {
                this.logger.log(`▶️ [Job ${job.id}] Costco: Starting scrape for ${categoryLabel}...`);
                await job.log(`Starting Costco scrape: ${categoryLabel}`);
                const costcoProducts = await this.costcoScraper.scrapeCategory(url, progress);
                if (costcoProducts && costcoProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(costcoProducts);
                }
                const costcoElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Costco: Finished in ${costcoElapsed}s`);
                await job.log(`Completed: ${costcoProducts.length} products in ${costcoElapsed}s`);
                return { status: 'completed' };
            }

            default:
                this.logger.warn(`❓ Unknown job name: ${job.name}`);
                return { status: 'unknown' };
        }
    }
}
