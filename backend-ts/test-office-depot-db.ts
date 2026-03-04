import { PrismaService } from './src/prisma.service';
import { ProductRepository } from './src/scraper/repositories/product.repository';
import { OfficeDepotScraper } from './src/scraper/crawlers/office-depot.scraper';

async function runTest() {
    console.log('Starting Office Depot Scraper test with DB connection...');

    // Create actual Prisma Service
    const prisma = new PrismaService();
    await prisma.onModuleInit();

    const repo = new ProductRepository(prisma);
    const scraper = new OfficeDepotScraper(repo);

    // Test URL
    const testUrl = 'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0';

    try {
        const results = await scraper.scrapeCategory(testUrl);
        console.log(`Total scraped in test: ${results.length}`);
    } catch (e) {
        console.error('Error during scrape:', e);
    } finally {
        await prisma.$disconnect();
    }
}

runTest().then(() => console.log('Test complete.'));
