import { CoppelScraper } from './src/scraper/crawlers/coppel.scraper';

class MockRepo {
    async bulkUpsert(products: any[]) {
        console.log(`\n[MOCK] bulkUpsert called with ${products.length} products`);
        if (products.length > 0) {
            console.log('Sample item:');
            console.log(JSON.stringify(products[0], null, 2));
        }
    }
}

async function runTest() {
    console.log('Starting TS CoppelScraper test...');
    const repo = new MockRepo() as any;
    const scraper = new CoppelScraper(repo);

    // Testing specific category
    const url = 'https://www.coppel.com/ct/celulares/celulares-por-marca/cat000032';
    const products = await scraper.scrapeCategory(url);

    console.log(`\nDone! Scraped a total of ${products.length} products.`);
    process.exit(0);
}

runTest().catch(e => {
    console.error(e);
    process.exit(1);
});
