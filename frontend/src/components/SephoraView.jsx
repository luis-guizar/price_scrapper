import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Search, ExternalLink, Sparkles, TrendingDown, Tag } from 'lucide-react'
import PriceHistoryChart from './PriceHistoryChart'

// A product counts as a "real deal" if it's at its historical low, or sitting
// meaningfully below its own typical (median) price. This sidesteps the store's
// original_price anchor entirely — the discount is proven against our own history.
const DEAL_MEDIAN_THRESHOLD = 3 // percent below median

export default function SephoraView() {
    const [deals, setDeals] = useState([])
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [selected, setSelected] = useState(null)
    const [history, setHistory] = useState([])

    useEffect(() => {
        let cancelled = false
        setLoading(true)
        Promise.all([
            axios.get('/api/products/deals', { params: { source: 'sephora', min_history_count: 2, limit: 200 } }),
            axios.get('/api/products', { params: { source: 'sephora', limit: 300, sort_by: 'newest' } }),
        ])
            .then(([dealsRes, prodRes]) => {
                if (cancelled) return
                setDeals(Array.isArray(dealsRes.data) ? dealsRes.data : [])
                setProducts(prodRes.data?.data ?? prodRes.data ?? [])
            })
            .catch(err => console.error('Error loading Sephora data:', err))
            .finally(() => !cancelled && setLoading(false))
        return () => { cancelled = true }
    }, [])

    useEffect(() => {
        if (!selected) { setHistory([]); return }
        axios.get(`/api/products/${selected.id}/history`)
            .then(res => {
                const data = (Array.isArray(res.data) ? res.data : []).map(item => ({
                    ...item,
                    date: new Date(item.timestamp).toLocaleDateString() + ' ' + new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }))
                setHistory(data)
            })
            .catch(err => console.error('Error loading history:', err))
    }, [selected])

    // Only surface products that are actually a deal right now, best first.
    const realDeals = useMemo(
        () => deals.filter(d => d.is_historical_low || d.pct_below_median >= DEAL_MEDIAN_THRESHOLD),
        [deals]
    )

    const filteredProducts = useMemo(() => {
        const q = search.trim().toLowerCase()
        if (!q) return products
        return products.filter(p => (p.name || '').toLowerCase().includes(q))
    }, [products, search])

    // Historical low/high for the selected product's chart reference lines.
    const selectedRange = useMemo(() => {
        if (history.length < 2) return { min: null, max: null }
        const prices = history.map(h => h.price)
        return { min: Math.min(...prices), max: Math.max(...prices) }
    }, [history])

    return (
        <div className="space-y-6">

            {/* Intro banner */}
            <div className="bg-gradient-to-r from-rose-500/10 to-pink-500/5 border border-rose-400/20 rounded-2xl p-5 md:p-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-rose-400/15 rounded-xl text-rose-300">
                        <Sparkles size={24} />
                    </div>
                    <div>
                        <h2 className="text-lg md:text-xl font-bold text-rose-100 tracking-tight">Sephora — Price Trends & Real Deals</h2>
                        <p className="text-xs md:text-sm text-rose-200/60 mt-0.5">
                            Discounts proven against each product's own price history — not the store's list price.
                        </p>
                    </div>
                </div>
            </div>

            {/* Real Deals section */}
            <section>
                <div className="flex items-center gap-2 mb-3">
                    <Tag size={16} className="text-rose-400" />
                    <h3 className="font-semibold text-slate-200 text-sm tracking-wide uppercase">Ofertas Reales · Real Deals Right Now</h3>
                    <span className="text-xs bg-slate-800/80 px-2.5 py-0.5 rounded-full text-slate-400 font-mono tabular-nums">{realDeals.length}</span>
                </div>

                {loading ? (
                    <div className="text-slate-500 text-sm py-8 text-center">Loading deals…</div>
                ) : realDeals.length === 0 ? (
                    <div className="bg-[#0d1524] border border-slate-700/50 rounded-2xl p-8 text-center">
                        <TrendingDown size={36} className="mx-auto mb-3 opacity-25 text-slate-500" />
                        <p className="text-sm text-slate-400 font-medium">No proven deals right now</p>
                        <p className="text-xs text-slate-600 mt-1">Prices are checked every 30 minutes — this fills up as products dip below their usual price.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {realDeals.map(d => (
                            <div
                                key={d.id}
                                onClick={() => setSelected(d)}
                                className={`group p-4 rounded-2xl border cursor-pointer transition-all duration-150 bg-[#0d1524] hover:border-rose-400/40 ${selected?.id === d.id ? 'border-rose-400/50 shadow-sm shadow-rose-900/20' : 'border-slate-700/50'}`}
                            >
                                <div className="flex items-start justify-between gap-2 mb-3">
                                    <h4 className="font-medium text-sm text-slate-200 leading-snug line-clamp-2">{d.name}</h4>
                                    <div className="flex items-center gap-1.5 shrink-0">
                                        {d.is_historical_low && (
                                            <span className="text-[10px] px-2 py-0.5 rounded-full border font-semibold bg-rose-400/10 border-rose-400/30 text-rose-300">
                                                Historical Low
                                            </span>
                                        )}
                                        {d.url && (
                                            <a
                                                href={d.url}
                                                target="_blank"
                                                rel="noreferrer"
                                                onClick={e => e.stopPropagation()}
                                                title="View on Sephora"
                                                className="p-1 rounded-full text-slate-500 hover:text-rose-300 hover:bg-rose-400/10 transition-colors"
                                            >
                                                <ExternalLink size={13} />
                                            </a>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-end justify-between">
                                    <div>
                                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">Current</span>
                                        <span className="text-2xl font-bold text-white tabular-nums">${d.current_price?.toLocaleString()}</span>
                                    </div>
                                    <div className="text-right">
                                        <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-sm tabular-nums">
                                            <TrendingDown size={14} />
                                            {Math.round(d.pct_below_median)}%
                                        </span>
                                        <span className="text-[10px] text-slate-500 block">vs typical</span>
                                    </div>
                                </div>

                                <div className="mt-3 pt-3 border-t border-slate-700/40 flex justify-between text-[11px] text-slate-500 tabular-nums">
                                    <span>Low <span className="text-rose-300">${d.min_price?.toLocaleString()}</span></span>
                                    <span>Typical <span className="text-slate-300">${Math.round(d.median_price).toLocaleString()}</span></span>
                                    <span>High <span className="text-slate-300">${d.max_price?.toLocaleString()}</span></span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* Trend browser */}
            <section>
                <div className="flex items-center gap-2 mb-3">
                    <Search size={16} className="text-slate-400" />
                    <h3 className="font-semibold text-slate-200 text-sm tracking-wide uppercase">Browse Price Trends</h3>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:h-[520px]">
                    {/* Product list */}
                    <div className="lg:col-span-1 bg-[#0d1524] rounded-2xl border border-slate-700/50 flex flex-col overflow-hidden shadow-card">
                        <div className="p-4 border-b border-slate-700/40">
                            <div className="relative">
                                <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                                <input
                                    type="text"
                                    placeholder="Search products…"
                                    className="input-base pl-7 pr-3 py-1.5 text-xs w-full"
                                    value={search}
                                    onChange={e => setSearch(e.target.value)}
                                />
                            </div>
                            <div className="mt-2 text-[11px] text-slate-500 tabular-nums">{filteredProducts.length} products</div>
                        </div>
                        <div className="overflow-y-auto flex-1 p-2 space-y-1.5 max-h-[50vh] lg:max-h-none">
                            {filteredProducts.map(p => (
                                <div
                                    key={p.id}
                                    onClick={() => setSelected(p)}
                                    className={`p-3 rounded-xl border cursor-pointer transition-all duration-150 hover:bg-slate-800/60 ${selected?.id === p.id ? 'bg-slate-800/80 border-rose-400/40' : 'border-transparent hover:border-slate-700/40'}`}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <h4 className="font-medium text-sm line-clamp-2 leading-snug text-slate-200">{p.name}</h4>
                                        {p.url && (
                                            <a
                                                href={p.url}
                                                target="_blank"
                                                rel="noreferrer"
                                                onClick={e => e.stopPropagation()}
                                                title="View on Sephora"
                                                className="shrink-0 p-1 rounded-full text-slate-500 hover:text-rose-300 hover:bg-rose-400/10 transition-colors"
                                            >
                                                <ExternalLink size={12} />
                                            </a>
                                        )}
                                    </div>
                                    <div className="mt-1.5 flex items-center justify-between">
                                        <span className="text-base font-bold text-white tabular-nums">${p.current_price?.toLocaleString()}</span>
                                        <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium bg-rose-400/10 border-rose-400/30 text-rose-400">🌸 Sephora</span>
                                    </div>
                                </div>
                            ))}
                            {!loading && filteredProducts.length === 0 && (
                                <div className="text-center text-slate-600 text-sm py-8">No products match your search</div>
                            )}
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="lg:col-span-2 bg-[#0d1524] rounded-2xl border border-slate-700/50 p-6 flex flex-col shadow-card">
                        {selected ? (
                            <>
                                <div className="flex justify-between items-start mb-6">
                                    <div className="min-w-0">
                                        <h2 className="text-lg font-bold text-slate-100 tracking-tight line-clamp-2">{selected.name}</h2>
                                        {selected.url && (
                                            <a href={selected.url} target="_blank" rel="noreferrer" className="text-sm text-rose-300 hover:text-rose-200 flex items-center gap-1 mt-1">
                                                View on Sephora <ExternalLink size={12} />
                                            </a>
                                        )}
                                    </div>
                                    <div className="text-right shrink-0 ml-4">
                                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Current</span>
                                        <span className="text-xl font-bold text-white tabular-nums">${selected.current_price?.toLocaleString()}</span>
                                    </div>
                                </div>

                                {history.length >= 2 ? (
                                    <div className="flex-1 w-full min-h-[300px] h-[320px] lg:h-auto">
                                        <PriceHistoryChart data={history} minPrice={selectedRange.min} maxPrice={selectedRange.max} />
                                    </div>
                                ) : (
                                    <div className="flex-1 flex flex-col items-center justify-center text-slate-600 gap-1">
                                        <TrendingDown size={40} className="mb-2 opacity-25" />
                                        <p className="text-sm font-medium text-slate-500">Not enough price history yet</p>
                                        <p className="text-xs text-slate-600">Only one price recorded so far — check back after a price change.</p>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-1">
                                <Sparkles size={48} className="mb-3 opacity-25 text-rose-400/40" />
                                <p className="text-sm font-medium text-slate-500">Select a product to view its price trend</p>
                                <p className="text-xs text-slate-600 mt-1">Pick a deal above or any product from the list</p>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    )
}
