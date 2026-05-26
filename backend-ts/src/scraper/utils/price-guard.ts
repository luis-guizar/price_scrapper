export interface PriceGuardRule {
    keywords: string[];
    maxPrice: number;
}

export function capUnreasonableOriginalPrice(
    title: string,
    currentPrice: number,
    originalPrice: number,
    rules: PriceGuardRule[],
    onCap?: (title: string, from: number, to: number) => void,
): number {
    const titleLower = title.toLowerCase();
    for (const rule of rules) {
        if (rule.keywords.some(k => titleLower.includes(k))) {
            if (originalPrice > rule.maxPrice) {
                const capped = Math.max(rule.maxPrice, currentPrice);
                if (capped !== originalPrice) onCap?.(title, originalPrice, capped);
                return capped;
            }
            break;
        }
    }
    return originalPrice;
}

export const ELECTRONICS_RULES: PriceGuardRule[] = [
    // --- TIER 1: ULTRA COMPUTING & WORKSTATIONS ---
    { keywords: ['macbook pro', 'mac studio', 'mac pro', 'imac pro'], maxPrice: 200000 },
    { keywords: ['macbook air', 'snapdragon x elite', 'core ultra 7', 'zenbook', 'yoga slim', 'yoga pro', 'surface laptop', 'xps'], maxPrice: 48000 },

    // --- TIER 2: HIGH-END HARDWARE COMPONENTS ---
    { keywords: ['rtx 5080', 'rtx 5090', 'rtx 4090', 'rtx 4080', 'intel core i9', 'core i9', 'core ultra 9', 'ryzen 9', 'ryzen ai 9'], maxPrice: 130000 },
    { keywords: ['tarjeta de video', 'tarjeta gráfica', 'gpu'], maxPrice: 65000 },

    // --- TIER 3: GAMING LAPTOPS & DESKTOPS ---
    { keywords: ['laptop gamer', 'laptop gaming', 'computadora gamer', 'computadora gaming', 'pc gamer', 'pc gaming', 'xtreme pc', 'grizzly pcg', 'predator', 'legion', 'rog strix', 'tuf gaming', 'omen', 'aero'], maxPrice: 85000 },

    // --- TIER 4: STANDARD LAPTOPS & DESKTOPS ---
    { keywords: ['all in one', 'aio', 'omnistudio', 'imac'], maxPrice: 60000 },
    { keywords: ['laptop', 'notebook', 'pc', 'computadora', 'computadora portátil', 'lap top'], maxPrice: 35000 },

    // --- TIER 5: PRINTERS & IMAGING ---
    { keywords: ['plotter', 'impresora industrial', 'duplicadora'], maxPrice: 60000 },
    { keywords: ['impresora térmica', 'impresora termica', 'qian térmica', 'qian termica', 'mini printer'], maxPrice: 2200 },
    { keywords: ['xerox b', 'brother dcp', 'deskjet', 'ink advantage', 'smart tank 5', 'ecotank l3', 'ecotank l1'], maxPrice: 4500 },
    { keywords: ['impresora', 'multifuncional', 'escáner', 'escaner', 'ecotank', 'smart tank', 'laserjet'], maxPrice: 9000 },

    // --- TIER 6: PRINTER CONSUMABLES ---
    { keywords: ['kit de tóner', 'kit de toner', 'paquete de toner', 'tóner pack'], maxPrice: 12000 },
    { keywords: ['tóner', 'toner'], maxPrice: 3200 },
    { keywords: ['hp 667', 'hp 664', 'hp 67', 'hp 662', 'cartucho de tinta', 'bote de tinta', 'botella de tinta', 'kit bote'], maxPrice: 1200 },

    // --- TIER 7: MONITOR DISPLAY SYSTEMS ---
    { keywords: ['monitor oled', 'monitor gaming oled', 'monitor ultra wide', 'ultrawide oled', 'odyssey g9'], maxPrice: 45000 },
    { keywords: ['monitor gaming', 'monitor gamer', 'pantalla gamer', 'pantalla gaming', 'monitor 4k', 'odyssey', '144hz', '240hz'], maxPrice: 22000 },
    { keywords: ['qian standard', 'sansui standard', 'monitor standard', 'monitor full hd', 'monitor fhd', 'sansui', 'qian', 'ghia', 'acteck', 'vorago'], maxPrice: 3200 },
    { keywords: ['monitor', 'pantalla para pc'], maxPrice: 12000 },

    // --- TIER 8: TABLETS ---
    { keywords: ['ipad pro', 'tab s9 ultra', 'tab s10 ultra', 'matepad pro'], maxPrice: 48000 },
    { keywords: ['ipad air', 'ipad mini', 'galaxy tab s', 'surface pro', 'yoga tab'], maxPrice: 32000 },
    { keywords: ['tablet', 'galaxy tab', 'matepad', 'ipad'], maxPrice: 16000 },

    // --- TIER 9: SMARTPHONES (Expanded Foldables/Premium) ---
    { keywords: ['iphone 17 pro max', 'iphone 16 pro max', 'galaxy z fold', 'z fold', 'pixel fold', 's26 ultra', 's25 ultra'], maxPrice: 60000 },
    { keywords: ['iphone 17 pro', 'iphone 16 pro', 'iphone 15 pro', 'motorola razr', 'galaxy z flip', 'z flip'], maxPrice: 45000 },
    { keywords: ['iphone', 'galaxy s26+', 'galaxy s25+', 'galaxy s', 'motorola edge', 'motorola signature'], maxPrice: 35000 },
    { keywords: ['smartphone', 'celular', 'teléfono', 'telefono'], maxPrice: 18000 },

    // --- TIER 10: TELEVISIONS (Added 98"+ limits) ---
    { keywords: ['microled', '8k', '100 pulgadas', '98 pulgadas', '97 pulgadas'], maxPrice: 400000 },
    { keywords: ['oled tv', 'qled tv', 'miniled tv', 'lg oled evo', 'televisión oled', 'television oled', '85 pulgadas', '86 pulgadas'], maxPrice: 150000 },
    { keywords: ['pantalla', 'tv', 'televisión', 'television', 'smart tv'], maxPrice: 45000 },

    // --- TIER 11: PHOTOGRAPHY & ACTION CAMS (Massive Spanish Expansion) ---
    { keywords: ['blackmagic', 'sony fx', 'ilme-fx', 'ilce-9', 'eos r5', 'eos r3', 'nikon z9', 'nikon z8'], maxPrice: 180000 }, // Pro Cinema & Flagships
    { keywords: ['cámara reflex', 'camara reflex', 'cámara sin espejo', 'camara sin espejo', 'cámara mirrorless', 'camara mirrorless', 'videocámara', 'cuerpo', 'lente', 'nikon z', 'sony alpha', 'canon eos r', 'fujifilm x', 'ilce'], maxPrice: 90000 }, // Enthusiast / Prosumer Mirrorless
    { keywords: ['cámara', 'camara', 'gopro', 'go pro', 'cámara de acción', 'camara de accion'], maxPrice: 15000 },

    // --- TIER 12: AUDIO SYSTEMS & SOUNDBARS (Expanded Premium Audio) ---
    { keywords: ['bose smart', 'sonos arc', 'sonos beam', 'sony ht', 'jbl bar', 'samsung hw-q', 'klipsch', 'polk', 'lg s9'], maxPrice: 35000 },
    { keywords: ['barra de sonido', 'soundbar', 'bocina', 'bocinas', 'bafle'], maxPrice: 12000 },

    // --- TIER 13: SMARTWATCHES & WEARABLES ---
    { keywords: ['garmin forerunner', 'garmin approach', 'garmin fenix', 'garmin epix', 'huawei watch ultimate', 'apple watch ultra', 'galaxy watch ultra'], maxPrice: 26000 },
    { keywords: ['apple watch', 'galaxy watch classic', 'galaxy watch pro', 'huawei watch pro'], maxPrice: 15000 },
    { keywords: ['reloj', 'smartwatch', 'galaxy watch', 'huawei watch'], maxPrice: 7000 },

    // --- TIER 14: HEADPHONES ---
    { keywords: ['airpods max', 'focal bathys'], maxPrice: 18000 },
    { keywords: ['airpods pro', 'sony wh', 'sony wf', 'bose quietcomfort', 'bose ultra'], maxPrice: 12000 },
    { keywords: ['audífonos', 'audifonos', 'auriculares', 'airpods'], maxPrice: 5000 },

    // --- TIER 15: HOME APPLIANCES ---
    { keywords: ['refrigerador french door', 'lavadora secadora', 'centro de lavado'], maxPrice: 85000 },
    { keywords: ['thermomix', 'robot de cocina'], maxPrice: 40000 },
    { keywords: ['refrigerador', 'lavadora', 'secadora', 'estufa', 'lavavajillas', 'nevera'], maxPrice: 30000 },
];

export const OFFICE_RULES: PriceGuardRule[] = [
    // Shared Computing Parity Match
    { keywords: ['macbook pro', 'mac studio', 'mac pro', 'imac pro'], maxPrice: 200000 },
    { keywords: ['macbook air', 'snapdragon x elite', 'core ultra 7', 'zenbook', 'yoga slim', 'yoga pro', 'surface laptop', 'xps'], maxPrice: 48000 },
    { keywords: ['rtx 5080', 'rtx 5090', 'rtx 4090', 'intel core i9', 'core ultra 9'], maxPrice: 130000 },
    { keywords: ['laptop gamer', 'laptop gaming', 'computadora gamer', 'computadora gaming', 'pc gamer', 'pc gaming'], maxPrice: 85000 },
    { keywords: ['all in one', 'aio', 'omnistudio'], maxPrice: 60000 },
    { keywords: ['laptop', 'notebook', 'computadora', 'computadora portátil'], maxPrice: 35000 },
    { keywords: ['ipad pro', 'tab s9 ultra'], maxPrice: 48000 },
    { keywords: ['ipad', 'tablet'], maxPrice: 16000 },

    // Displays & Office Monitors
    { keywords: ['monitor oled', 'monitor gaming'], maxPrice: 45000 },
    { keywords: ['monitor gaming', 'monitor gamer'], maxPrice: 22000 },
    { keywords: ['qian standard', 'sansui standard', 'monitor standard', 'monitor full hd', 'monitor fhd', 'sansui', 'qian', 'ghia', 'acteck', 'vorago'], maxPrice: 3200 },
    { keywords: ['pantalla', 'monitor'], maxPrice: 12000 },

    // Office Printers & Consumables 
    { keywords: ['plotter', 'impresora industrial'], maxPrice: 60000 },
    { keywords: ['impresora térmica', 'impresora termica', 'qian térmica', 'qian termica'], maxPrice: 2200 },
    { keywords: ['xerox b', 'brother dcp', 'deskjet'], maxPrice: 4500 },
    { keywords: ['impresora', 'multifuncional', 'escáner', 'escaner'], maxPrice: 9000 },
    { keywords: ['kit de tóner', 'kit de toner', 'tóner', 'toner', 'cartucho', 'tinta'], maxPrice: 1200 },

    // Ergonomic Infrastructure & Seating
    { keywords: ['herman miller', 'silla aeron', 'silla embody', 'steelcase'], maxPrice: 65000 },
    { keywords: ['silla ejecutiva', 'silla ergonomica', 'silla ergonómica'], maxPrice: 18000 },
    { keywords: ['silla de oficina', 'silla'], maxPrice: 8000 },

    // Office Desks
    { keywords: ['escritorio elevable', 'standing desk', 'escritorio electrico', 'escritorio eléctrico'], maxPrice: 25000 },
    { keywords: ['escritorio', 'mueble de oficina', 'archivero'], maxPrice: 12000 },
];

export const BEAUTY_RULES: PriceGuardRule[] = [
    { keywords: ['creed royal', 'creed perfume', 'baccarat rouge', 'tom ford private', 'clive christian'], maxPrice: 16000 },
    { keywords: ['perfume', 'eau de parfum', 'cologne', 'fragrance', 'loción', 'locion', 'eau de toilette'], maxPrice: 8000 },
    { keywords: ['gift set', 'coffret', 'estuche de regalo', 'set de belleza', 'kit de regalo'], maxPrice: 7000 },
    { keywords: ['set', 'kit'], maxPrice: 4500 },
    { keywords: ['la mer', 'skinceuticals', 'sisley paris'], maxPrice: 9000 },
    { keywords: ['serum', 'suero', 'retinol', 'vitamin c', 'vitamina c', 'moisturizer', 'crema facial'], maxPrice: 5000 },
    { keywords: ['palette', 'paleta de sombras', 'eyeshadow', 'blush', 'bronzer'], maxPrice: 3500 },
    { keywords: ['foundation', 'base de maquillaje', 'concealer', 'corrector', 'primer'], maxPrice: 2500 },
    { keywords: ['lipstick', 'labial', 'lip gloss', 'brillo labial', 'mascara', 'rímel', 'rimel', 'eyeliner'], maxPrice: 1500 },
];