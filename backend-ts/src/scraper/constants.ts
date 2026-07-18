export const OFFICE_DEPOT_CONFIG = {
    urls: [
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/computadoras-de-escritorio/c/04-037-0-0',
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Celulares/c/03-1-0-0',
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/laptops-y-macbook/c/04-039-0-0',
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Muebles-y-Decoraci%C3%B3n/Sillas/c/06-084-0-0',
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Impresi%C3%B3n/Impresoras%2C-Multifuncionales-y-Esc%C3%A1neres/c/07-100-0-0',
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/Electr%C3%B3nica/Pantallas/c/03-027-0-0',
        'https://www.officedepot.com.mx/officedepot/en/Categor%C3%ADa/Todas/computo/ipad-y-tablets/tablets/c/04-041-906-0',
    ],
};

export const COPPEL_CONFIG = {
    urls: [
        'https://www.coppel.com/ct/celulares/celulares-por-marca/cat000032?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/pantallas/cat000268?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/laptops/cat000166?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/computadoras-escritorio/cat000175?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/pc-gaming-accesorios/cat000138?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/monitores/cat000176?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/componentes/cat000233?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/tablets/cat000068?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/electronica/smartwatches/cat000328?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.coppel.com/ct/consolas-videojuegos/cat001063?pmNodeId=11408&prNodeId=11419&regionTelcel=6',
        'https://www.motoscoppel.mx/ct/motos-movilidad/motos/cat002551',
    ],
};

export const LIVERPOOL_CONFIG = {
    urls: [
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST10075558&page=1&Path=PLP&categoryName=Laptops',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST14457077&page=1&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST53117186&page=1&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CAT580066&page=1&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST46664340&page=1&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CAT670066&page=1&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST4818718&page=2&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST16779026&page=2&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST16779038&page=2&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST53117490&page=2',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST16778857&page=2',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST16778924&page=2',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST16778939&page=2&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST53450418&page=2&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST60647160&page=2&Path=PLP',
        'https://www.liverpool.com.mx/getPlpFilter?categoryId=CATST53118497&page=2&Path=PLP',
    ],
};

// Sephora MX uses a Constructor.io search API; the search term is the path
// segment (/search/<term>). Each term is scraped as a separate category so the
// friend's Sephora view covers makeup, skincare and fragrance — not just blush.
// Result counts verified live (2026-07-17): blush 153, labiales 239, base 160,
// corrector 99, perfume 124, serum 336, skincare 1460.
const SEPHORA_QS = 'c=ciojs-client-bundled-2.72.2&key=key_Y4DWcKVGsCyfyCID&i=0aad6209-0b7e-4efc-a9e6-a1c91a3f4620&s=1&page=1&num_results_per_page=52&filters%5BisExclusiveApp%5D=False';
const SEPHORA_TERMS = ['blush', 'labiales', 'base', 'corrector', 'perfume', 'serum', 'skincare'];

export const SEPHORA_CONFIG = {
    urls: SEPHORA_TERMS.map(term => `https://ac.cnstrc.com/search/${term}?${SEPHORA_QS}`),
};

// Chedraui MX runs on VTEX; its standard catalog REST API returns clean product
// JSON (the old persisted-query GraphQL endpoint now 404s, which is why the
// legacy Python scraper was disabled). Each URL is a category first page; the
// scraper paginates via _from/_to. Category slugs + counts verified live
// (2026-07-18): tecnologia 2489, electrodomesticos-y-linea-blanca 1219,
// jugueteria 3415.
const CHEDRAUI_CATEGORIES = [
    'tecnologia',
    'electrodomesticos-y-linea-blanca',
    'jugueteria',
];

export const CHEDRAUI_CONFIG = {
    baseUrl: 'https://www.chedraui.com.mx',
    urls: CHEDRAUI_CATEGORIES.map(
        cat =>
            `https://www.chedraui.com.mx/api/catalog_system/pub/products/search/${cat}?O=OrderByScoreDESC&_from=0&_to=49`,
    ),
};

// Sears MX exposes a public Algolia search key (read from its Next.js config,
// 2026-07-18). This is a stable JSON API — ban-proof, no HTML parsing. Each
// "url" is just a search term; the scraper POSTs it to Algolia and paginates.
// Sears is a marketplace (Grupo Carso), so results include third-party sellers.
export const SEARS_CONFIG = {
    baseUrl: 'https://www.sears.com.mx',
    algolia: {
        appId: '6M62U1ZBKU',
        apiKey: '6698ccede119391b5f6db5c39352b1f2',
        index: 'sears',
    },
    urls: [
        'pantalla',
        'laptop',
        'celular',
        'refrigerador',
        'lavadora',
        'audifonos',
        'smartwatch',
        'tablet',
        'consola',
        'licuadora',
    ],
};

// Costco MX runs Spartacus (SAP Commerce); its OCC REST API serves product JSON
// (base site "mexico"), discovered via browser network capture 2026-07-18. The
// search response exposes both `price` (current) and `basePrice` (regular/MSRP),
// so genuine discounts are captured and feed the alert rule. Each "url" is a
// search term.
export const COSTCO_CONFIG = {
    baseUrl: 'https://www.costco.com.mx',
    urls: [
        'pantalla',
        'laptop',
        'refrigerador',
        'lavadora',
        'colchon',
        'audifonos',
        'tablet',
        'freidora',
        'bicicleta',
        'llanta',
    ],
};

export const MELI_CONFIG = {
    urls: [
        'https://listado.mercadolibre.com.mx/computacion/componentes-pc/tarjetas/tarjetas-video/fabricante-amd/nuevo/gpu-amd_Tienda_all_NoIndex_True#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D12%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D58%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/computacion/laptops-accesorios/laptops/laptop-gamer_Tienda_all_NoIndex_True#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D15%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D1354%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/_Container_ao-renueva-tu-cel-lo-mas-buscado#c_container_id=MLM1059162-1&c_id=%2Fsplinter%2Fspecial-withoutlabel&c_element_order=1&c_campaign=lo-mas-vendido&c_label=%2Fsplinter%2Fspecial-withoutlabel&c_uid=44e76250-1195-11f1-b859-fd337382bc55&c_element_id=44e76250-1195-11f1-b859-fd337382bc55&c_content_origin=splinter-default&c_content_type=default&c_global_position=9&deal_print_id=44d93180-1195-11f1-ab81-95c797f22285&c_tracking_id=44d93180-1195-11f1-ab81-95c797f22285',
        'https://listado.mercadolibre.com.mx/computacion/componentes-pc/procesador-amd-ryzen_Tienda_all_NoIndex_True?sb=all_mercadolibre#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D10%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D223%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/computacion/componentes-pc/procesador-intel-core_Tienda_all_NoIndex_True?sb=all_mercadolibre#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D13%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D158%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/camaras-accesorios/camaras/camaras-digitales/_Tienda_all_NoIndex_True?original_category_landing=true#unapplied_filter_id%3DBRAND%26unapplied_filter_name%3DMarca%26unapplied_value_id%3D995%26unapplied_value_name%3DSony%26unapplied_autoselect%3Dfalse',
        'https://listado.mercadolibre.com.mx/juegos-juguetes/montables-ninos/scooters/electricos/scooter-electrico_Tienda_all_NoIndex_True?sb=all_mercadolibre#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D18%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D785%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/computacion/laptops-accesorios/laptops/reacondicionado/laptop-reacondicionada_Tienda_all_NoIndex_True_SHIPPING*ORIGIN_10215068?sb=all_mercadolibre#applied_filter_id%3DSHIPPING_ORIGIN%26applied_filter_name%3DOrigen+del+env%C3%ADo%26applied_filter_order%3D12%26applied_value_id%3D10215068%26applied_value_name%3DLocal%26applied_value_order%3D2%26applied_value_results%3D144%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/computacion/laptops-accesorios/laptops/apple/reacondicionado/macbook-reacondicionada_Tienda_all_NoIndex_True?sb=all_mercadolibre#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D10%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D12%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/celulares-telefonia/celulares-smartphones/reacondicionado/smartphone-reacondicionado_Tienda_all_NoIndex_True?sb=all_mercadolibre#applied_filter_id%3Dofficial_store%26applied_filter_name%3DTiendas+oficiales%26applied_filter_order%3D11%26applied_value_id%3Dall%26applied_value_name%3DSolo+tiendas+oficiales%26applied_value_order%3D1%26applied_value_results%3D9%26is_custom%3Dfalse',
        'https://listado.mercadolibre.com.mx/computacion/componentes-pc/tarjetas/tarjetas-video/fabricante-nvidia/nuevo/gpu-nvidia_Tienda_all_NoIndex_True_SHIPPING*ORIGIN_10215068#applied_filter_id%3DSHIPPING_ORIGIN%26applied_filter_name%3DOrigen+del+env%C3%ADo%26applied_filter_order%3D9%26applied_value_id%3D10215068%26applied_value_name%3DLocal%26applied_value_order%3D2%26applied_value_results%3D142%26is_custom%3Dfalse'
    ],
};
