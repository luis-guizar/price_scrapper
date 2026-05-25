import { Processor, WorkerHost } from '@nestjs/bullmq';
import { Job } from 'bullmq';
import { Logger } from '@nestjs/common';
import { OfficeDepotScraper } from './crawlers/office-depot.scraper';
import { CoppelScraper } from './crawlers/coppel.scraper';
import { LiverpoolScraper } from './crawlers/liverpool.scraper';
import { MeliScraper } from './crawlers/meli.scraper';
import { SephoraScraper } from './crawlers/sephora.scraper';
import { AlertService } from '../alert.service';

@Processor('scraper-tasks', { concurrency: 1 })
export class ScraperProcessor extends WorkerHost {
    private readonly logger = new Logger(ScraperProcessor.name);

    constructor(
        private readonly officeDepotScraper: OfficeDepotScraper,
        private readonly coppelScraper: CoppelScraper,
        private readonly liverpoolScraper: LiverpoolScraper,
        private readonly meliScraper: MeliScraper,
        private readonly sephoraScraper: SephoraScraper,
        private readonly alertService: AlertService
    ) {
        super();
    }

    async process(job: Job<any, any, string>): Promise<any> {
        const startTime = Date.now();
        const { url } = job.data;
        const categoryLabel = url ? url.split('/').pop()?.substring(0, 20) : 'unknown';

        switch (job.name) {
            case 'scrape:officedepot':
                this.logger.log(`▶️ [Job ${job.id}] Office Depot: Starting scrape for ${categoryLabel}...`);
                const odProducts = await this.officeDepotScraper.scrapeCategory(url);
                const odElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Office Depot: Finished in ${odElapsed}s`);
                return { status: 'completed' };

            case 'scrape:coppel':
                this.logger.log(`▶️ [Job ${job.id}] Coppel: Starting scrape for ${categoryLabel}...`);
                const products = await this.coppelScraper.scrapeCategory(url);

                if (products && products.length > 0) {
                    await this.alertService.checkAndSendAlerts(products);
                }

                const coppelElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Coppel: Finished in ${coppelElapsed}s`);
                return { status: 'completed' };

            case 'scrape:liverpool':
                this.logger.log(`▶️ [Job ${job.id}] Liverpool: Starting scrape for ${categoryLabel}...`);
                const liverpoolProducts = await this.liverpoolScraper.scrapeCategory(url);

                if (liverpoolProducts && liverpoolProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(liverpoolProducts);
                }

                const liverpoolElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Liverpool: Finished in ${liverpoolElapsed}s`);
                return { status: 'completed' };

            case 'scrape:meli':
                this.logger.log(`▶️ [Job ${job.id}] MercadoLibre: Starting scrape for ${categoryLabel}...`);
                const meliProducts = await this.meliScraper.scrapeCategory(url);

                if (meliProducts && meliProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(meliProducts);
                }

                const meliElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] MercadoLibre: Finished in ${meliElapsed}s`);
                return { status: 'completed' };


            case 'scrape:sephora':
                this.logger.log(`▶️ [Job ${job.id}] Sephora: Starting scrape for ${categoryLabel}...`);
                const sephoraProducts = await this.sephoraScraper.scrapeCategory(url);

                if (sephoraProducts && sephoraProducts.length > 0) {
                    await this.alertService.checkAndSendAlerts(sephoraProducts);
                }

                const sephoraElapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                this.logger.log(`✅ [Job ${job.id}] Sephora: Finished in ${sephoraElapsed}s`);
                return { status: 'completed' };

            default:
                this.logger.warn(`❓ Unknown job name: ${job.name}`);
                return { status: 'unknown' };
        }
    }
}
