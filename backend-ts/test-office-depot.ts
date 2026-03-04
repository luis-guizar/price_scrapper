import { OfficeDepotScraper } from './src/scraper/crawlers/office-depot.scraper';
import { ProductRepository } from './src/scraper/repositories/product.repository';
// Mock repository
class MockProductRepository extends ProductRepository {
    constructor() {
        super(null as any); // Pass null for PrismaService
    }
    async bulkUpsert(products: any[]) {
        console.log(`Mock bulkUpsert called with ${products.length} products`);
        console.log('Sample product:', products[0]);
    }
}

async function runTest() {
    console.log('Starting Office Depot Scraper test...');
    const repo = new MockProductRepository();
    const scraper = new OfficeDepotScraper(repo);

    // Test URL
    const testUrl = 'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0';

    try {
        const results = await scraper.scrapeCategory(testUrl);
        console.log(`Total scraped in test: ${results.length}`);
    } catch (e) {
        console.error('Error during scrape:', e);
    }
}

runTest().then(() => console.log('Test complete.'));
