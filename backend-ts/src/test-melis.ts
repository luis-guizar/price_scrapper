const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
    const page = await context.newPage();
    try {
        await page.goto('https://listado.mercadolibre.com.mx/computacion/componentes-pc/procesador-amd-ryzen_Tienda_all_NoIndex_True_Desde_49', { waitUntil: 'domcontentloaded', timeout: 30000 });

        const productsCount = await page.evaluate(() => {
            return document.querySelectorAll('.ui-search-layout__item').length;
        });
        console.log('Products found with _Desde_49 at the end of path:', productsCount);

    } catch (e) {
        console.error(e);
    }
    await browser.close();
})();
