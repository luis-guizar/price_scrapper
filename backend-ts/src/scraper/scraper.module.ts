import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { ScraperController } from './scraper.controller';
import { PrismaService } from '../prisma.service';
import { ProductRepository } from './repositories/product.repository';
import { OfficeDepotScraper } from './crawlers/office-depot.scraper';
import { CoppelScraper } from './crawlers/coppel.scraper';
import { LiverpoolScraper } from './crawlers/liverpool.scraper';
import { MeliScraper } from './crawlers/meli.scraper';
import { SephoraScraper } from './crawlers/sephora.scraper';
import { ScraperProcessor } from './scraper.processor';
import { ScraperScheduleService } from './scraper.schedule';

import { AlertService } from '../alert.service';

@Module({
    imports: [
        BullModule.registerQueue({
            name: 'scraper-tasks',
            defaultJobOptions: {
                removeOnComplete: { count: 100 },
                removeOnFail: { count: 50 },
                attempts: 2,
                backoff: { type: 'fixed', delay: 30_000 },
            },
        }),
    ],
    controllers: [ScraperController],
    providers: [PrismaService, ProductRepository, OfficeDepotScraper, CoppelScraper, LiverpoolScraper, MeliScraper, SephoraScraper, ScraperProcessor, ScraperScheduleService, AlertService],
    exports: [ProductRepository, OfficeDepotScraper, CoppelScraper, LiverpoolScraper, MeliScraper, SephoraScraper],
})
export class ScraperModule { }
