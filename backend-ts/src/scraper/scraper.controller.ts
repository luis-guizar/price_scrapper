import { Controller, Post } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { OFFICE_DEPOT_CONFIG, COPPEL_CONFIG, LIVERPOOL_CONFIG, MELI_CONFIG, SEPHORA_CONFIG, CHEDRAUI_CONFIG, SEARS_CONFIG, COSTCO_CONFIG } from './constants';

@Controller('scraper')
export class ScraperController {
    constructor(@InjectQueue('scraper-tasks') private scraperQueue: Queue) { }

    @Post('test-scrape/officedepot')
    async triggerTestScrape() {
        const urls = OFFICE_DEPOT_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:officedepot', {
                url: url,
            });
        }

        return {
            message: 'Full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/coppel')
    async triggerCoppelTestScrape() {
        const urls = COPPEL_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:coppel', {
                url: url,
            });
        }

        return {
            message: 'Coppel full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/liverpool')
    async triggerLiverpoolTestScrape() {
        const urls = LIVERPOOL_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:liverpool', {
                url: url,
            });
        }

        return {
            message: 'Liverpool full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/sephora')
    async triggerSephoraTestScrape() {
        const urls = SEPHORA_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:sephora', { url });
        }

        return {
            message: 'Sephora full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/meli')
    async triggerMeliTestScrape() {
        const urls = MELI_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:meli', {
                url: url,
            });
        }

        return {
            message: 'MercadoLibre full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/chedraui')
    async triggerChedrauiTestScrape() {
        const urls = CHEDRAUI_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:chedraui', { url });
        }

        return {
            message: 'Chedraui full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/sears')
    async triggerSearsTestScrape() {
        const urls = SEARS_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:sears', { url });
        }

        return {
            message: 'Sears full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }

    @Post('test-scrape/costco')
    async triggerCostcoTestScrape() {
        const urls = COSTCO_CONFIG.urls;

        for (const url of urls) {
            await this.scraperQueue.add('scrape:costco', { url });
        }

        return {
            message: 'Costco full pass triggered',
            jobCount: urls.length,
            urls: urls
        };
    }
}
