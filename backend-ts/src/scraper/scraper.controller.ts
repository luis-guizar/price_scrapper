import { Controller, Post } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { OFFICE_DEPOT_CONFIG, COPPEL_CONFIG, LIVERPOOL_CONFIG, MELI_CONFIG } from './constants';

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
}
