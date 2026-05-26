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
    if (rule.keywords.some((k) => titleLower.includes(k))) {
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
  // Apple & Premium Computing (Top spec desktop/pro setups)
  {
    keywords: ['macbook pro', 'mac studio', 'imac pro', 'mac pro'],
    maxPrice: 200000,
  },
  { keywords: ['macbook air'], maxPrice: 45000 },
  {
    keywords: [
      'laptop gaming',
      'alienware',
      'predator',
      'legion',
      'rog strix',
      'razer blade',
      'msi titan',
    ],
    maxPrice: 120000,
  },
  {
    keywords: [
      'laptop',
      'notebook',
      'pc',
      'computadora',
      'computadora portátil',
      'lap top',
    ],
    maxPrice: 35000,
  },

  // PC Components (High-end GPUs can skew pricing heavily)
  {
    keywords: [
      'rtx 4090',
      'rtx 5090',
      'tarjeta de video',
      'tarjeta gráfica',
      'tarjeta grafica',
      'gpu',
    ],
    maxPrice: 65000,
  },

  // Tablets
  { keywords: ['ipad pro'], maxPrice: 75000 },
  { keywords: ['ipad air', 'ipad mini'], maxPrice: 28000 },
  { keywords: ['galaxy tab s', 'surface pro'], maxPrice: 38000 },
  { keywords: ['tablet', 'galaxy tab', 'ipad'], maxPrice: 18000 },

  // Smartphones (Reflecting 2026 market limits for premium tier & folds)
  {
    keywords: [
      'iphone 17 pro max',
      'iphone 16 pro max',
      'galaxy z fold',
      'z fold',
      'pixel fold',
    ],
    maxPrice: 60000,
  },
  {
    keywords: [
      'iphone 17 pro',
      'iphone 16 pro',
      'galaxy s26 ultra',
      'galaxy s25 ultra',
      's26 ultra',
      's25 ultra',
    ],
    maxPrice: 45000,
  },
  { keywords: ['iphone'], maxPrice: 28000 },
  {
    keywords: ['smartphone', 'celular', 'teléfono', 'telefono', 'galaxy s'],
    maxPrice: 22000,
  },

  // TVs & Displays
  { keywords: ['microled', '8k'], maxPrice: 400000 },
  {
    keywords: ['oled', 'qled', 'miniled', 'mini-led', 'lg oled evo'],
    maxPrice: 150000,
  },
  {
    keywords: ['pantalla', 'tv', 'televisión', 'television', 'smart tv'],
    maxPrice: 45000,
  },

  // Appliances & Smart Kitchen Tech
  {
    keywords: [
      'refrigerador french door',
      'lavadora secadora',
      'centro de lavado',
    ],
    maxPrice: 85000,
  },
  { keywords: ['thermomix', 'robot de cocina'], maxPrice: 40000 },
  {
    keywords: [
      'refrigerador',
      'lavadora',
      'secadora',
      'estufa',
      'lavavajillas',
      'nevera',
    ],
    maxPrice: 30000,
  },

  // Wearables & Premium Personal Care Tech
  { keywords: ['apple watch ultra'], maxPrice: 25000 },
  {
    keywords: [
      'dyson airwrap',
      'dyson supersonic',
      'dyson airstrait',
      'airwrap styler',
    ],
    maxPrice: 20000,
  },
  {
    keywords: [
      'apple watch',
      'galaxy watch ultra',
      'garmin fenix',
      'garmin epix',
    ],
    maxPrice: 20000,
  },
  {
    keywords: ['reloj', 'smartwatch', 'galaxy watch', 'huawei watch'],
    maxPrice: 12000,
  },

  // Audio & Headphones
  { keywords: ['airpods max', 'focal bathys'], maxPrice: 18000 },
  {
    keywords: [
      'airpods pro',
      'sony wh',
      'sony wf',
      'bose quietcomfort',
      'bose ultra',
    ],
    maxPrice: 12000,
  },
  {
    keywords: [
      'audífonos',
      'audifonos',
      'auriculares',
      'airpods',
      'bocina',
      'bocinas',
    ],
    maxPrice: 7000,
  },

  // Gaming & Monitors
  { keywords: ['monitor oled', 'monitor gaming'], maxPrice: 40000 },
  { keywords: ['monitor'], maxPrice: 15000 },
  { keywords: ['playstation 5 pro', 'ps5 pro'], maxPrice: 25000 },
  {
    keywords: [
      'consola',
      'nintendo switch',
      'playstation 5',
      'ps5',
      'xbox series x',
      'xbox series s',
      'nintendo',
      'xbox',
    ],
    maxPrice: 18000,
  },
];

export const BEAUTY_RULES: PriceGuardRule[] = [
  // Luxury & Niche Fragrances (e.g., Creed, Tom Ford Private Blend, MFK)
  {
    keywords: [
      'creed royal',
      'creed perfume',
      'baccarat rouge',
      'tom ford private',
      'clive christian',
      'acqua di parma',
    ],
    maxPrice: 16000,
  },
  {
    keywords: [
      'perfume',
      'eau de parfum',
      'cologne',
      'fragrance',
      'loción',
      'locion',
      'eau de toilette',
    ],
    maxPrice: 8000,
  },

  // Premium Gift Sets
  {
    keywords: [
      'gift set',
      'coffret',
      'estuche de regalo',
      'set de belleza',
      'kit de regalo',
    ],
    maxPrice: 7000,
  },
  { keywords: ['set', 'kit'], maxPrice: 4500 },

  // Ultra-Premium Skincare (e.g., La Mer, SkinCeuticals)
  { keywords: ['la mer', 'skinceuticals', 'sisley paris'], maxPrice: 9000 },
  {
    keywords: [
      'serum',
      'suero',
      'retinol',
      'vitamin c',
      'vitamina c',
      'moisturizer',
      'crema antiedad',
      'crema facial',
    ],
    maxPrice: 5000,
  },

  // Cosmetics & Makeup
  {
    keywords: ['palette', 'paleta de sombras', 'eyeshadow', 'blush', 'bronzer'],
    maxPrice: 3500,
  },
  {
    keywords: [
      'foundation',
      'base de maquillaje',
      'concealer',
      'corrector',
      'primer',
    ],
    maxPrice: 2500,
  },
  {
    keywords: [
      'lipstick',
      'labial',
      'lip gloss',
      'brillo labial',
      'mascara',
      'rímel',
      'rimel',
      'eyeliner',
      'delineador',
    ],
    maxPrice: 1500,
  },
];

export const OFFICE_RULES: PriceGuardRule[] = [
  // Computing duplicates (Kept to ensure matching parity within Office scope)
  {
    keywords: ['macbook pro', 'mac studio', 'imac pro', 'mac pro'],
    maxPrice: 200000,
  },
  { keywords: ['macbook air'], maxPrice: 45000 },
  { keywords: ['laptop gaming', 'alienware'], maxPrice: 120000 },
  {
    keywords: ['laptop', 'notebook', 'computadora', 'computadora portátil'],
    maxPrice: 35000,
  },
  { keywords: ['ipad pro'], maxPrice: 75000 },
  { keywords: ['ipad', 'tablet'], maxPrice: 18000 },

  // Displays
  { keywords: ['monitor oled', 'monitor gaming'], maxPrice: 40000 },
  { keywords: ['pantalla', 'monitor'], maxPrice: 15000 },

  // Printing & Scanning Equipment
  { keywords: ['plotter', 'impresora industrial'], maxPrice: 60000 },
  {
    keywords: ['impresora', 'multifuncional', 'escáner', 'escaner'],
    maxPrice: 20000,
  },

  // Ergonomic Infrastructure & Seating
  {
    keywords: ['herman miller', 'silla aeron', 'silla embody', 'steelcase'],
    maxPrice: 65000,
  },
  {
    keywords: ['silla ejecutiva', 'silla ergonomica', 'silla ergonómica'],
    maxPrice: 18000,
  },
  { keywords: ['silla de oficina', 'silla'], maxPrice: 8000 },

  // Desks & Office Furniture
  {
    keywords: [
      'escritorio elevable',
      'standing desk',
      'escritorio electrico',
      'escritorio eléctrico',
    ],
    maxPrice: 25000,
  },
  {
    keywords: ['escritorio', 'mueble de oficina', 'archivero'],
    maxPrice: 12000,
  },
];
