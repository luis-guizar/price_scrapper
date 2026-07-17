export const SOURCE_CONFIG = {
    keepa: { label: 'Amazon', color: 'from-orange-500 to-orange-600', icon: '📦', bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400' },
    promodescuentos: { label: 'PromoDescuentos', color: 'from-red-600 to-red-700', icon: '🔥', bg: 'bg-red-600/10 border-red-600/30 text-red-400' },
    officedepot: { label: 'Office Depot', color: 'from-red-400 to-red-500', icon: '🖨️', bg: 'bg-red-500/10 border-red-500/30 text-red-400' },
    cyberpuerta: { label: 'CyberPuerta', color: 'from-green-500 to-green-600', icon: '💻', bg: 'bg-green-500/10 border-green-500/30 text-green-400' },
    chedraui: { label: 'Chedraui', color: 'from-orange-400 to-orange-500', icon: '🏬', bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400' },
    elektra: { label: 'Elektra', color: 'from-purple-500 to-purple-600', icon: '⚡', bg: 'bg-purple-500/10 border-purple-500/30 text-purple-400' },
    soriana: { label: 'Soriana', color: 'from-red-500 to-red-600', icon: '🛒', bg: 'bg-red-500/10 border-red-500/30 text-red-400' },
    coppel: { label: 'Coppel', color: 'from-blue-500 to-blue-600', icon: '🔵', bg: 'bg-blue-500/10 border-blue-500/30 text-blue-400' },
    liverpool: { label: 'Liverpool', color: 'from-pink-500 to-pink-600', icon: '💗', bg: 'bg-pink-500/10 border-pink-500/30 text-pink-400' },
    mercadolibre: { label: 'MercadoLibre', color: 'from-yellow-400 to-yellow-500', icon: '🤝', bg: 'bg-yellow-400/10 border-yellow-400/30 text-yellow-500' },
    sephora: { label: 'Sephora', color: 'from-rose-400 to-rose-500', icon: '🌸', bg: 'bg-rose-400/10 border-rose-400/30 text-rose-400' },
    other: { label: 'Other', color: 'from-slate-500 to-slate-600', icon: '🔗', bg: 'bg-slate-500/10 border-slate-500/30 text-slate-400' },
}

export function getSourceBadge(source) {
    return SOURCE_CONFIG[source] || SOURCE_CONFIG.other
}
