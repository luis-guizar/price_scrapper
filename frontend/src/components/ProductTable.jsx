import React, { useState, useEffect } from 'react'
import { Search, Trash2, ExternalLink, Filter, ChevronLeft, ChevronRight, X, ListFilter, Bell, BellOff, Edit2 } from 'lucide-react'

export default function ProductTable({ products, onDelete, onToggleActive, onUpdateAnchorPrice, onSearch, pagination, onPageChange, activeFilters }) {
    // Local state for inputs
    const [search, setSearch] = useState('')
    const [sourceFilter, setSourceFilter] = useState('')
    const [minPrice, setMinPrice] = useState('')
    const [maxPrice, setMaxPrice] = useState('')
    const [sortBy, setSortBy] = useState('newest')
    const [exclude, setExclude] = useState('')
    const [showExclude, setShowExclude] = useState(false)
    const [showAdvanced, setShowAdvanced] = useState(false)

    // Sync local state with activeFilters when they change (e.g. initial load or external update)
    useEffect(() => {
        if (activeFilters) {
            setSearch(activeFilters.search || '')
            setSourceFilter(activeFilters.source || '')
            setMinPrice(activeFilters.minPrice || '')
            setMaxPrice(activeFilters.maxPrice || '')
            setSortBy(activeFilters.sortBy || 'newest')
            setExclude(activeFilters.exclude || '')
            if (activeFilters.exclude) setShowExclude(true)
        }
    }, [activeFilters])

    const handleSearch = () => {
        onSearch({
            search,
            source: sourceFilter,
            minPrice,
            maxPrice,
            sortBy,
            exclude: showExclude ? exclude : ''
        })
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSearch()
        }
    }

    const clearFilters = () => {
        setSearch('')
        setSourceFilter('')
        setMinPrice('')
        setMaxPrice('')
        setSortBy('newest')
        setExclude('')
        setShowExclude(false)
        onSearch({ search: '', source: '', minPrice: '', maxPrice: '', sortBy: 'newest', exclude: '' })
    }

    return (
        <div className="bg-[#0d1524] rounded-2xl border border-slate-700/50 flex flex-col h-full overflow-hidden shadow-card">

            {/* Toolbar */}
            <div className="px-5 py-4 border-b border-slate-700/40 flex flex-col gap-4">

                {/* Top Row: Search & Main Actions */}
                <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                    <h3 className="font-semibold text-base text-slate-200 whitespace-nowrap hidden md:block tracking-tight">All Tracked Products</h3>

                    <div className="flex items-center gap-2 w-full">
                        {/* Search Box */}
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                            <input
                                type="text"
                                placeholder="Search products..."
                                className="input-base pl-9 pr-4 py-2 text-sm w-full"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>

                        <button
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className={`p-2 rounded-lg border transition-all duration-150 ${showAdvanced ? 'bg-blue-600/15 border-blue-500/50 text-blue-300 shadow-sm shadow-blue-900/20' : 'bg-slate-950 border-slate-700/50 text-slate-400 hover:text-slate-200 hover:border-slate-600'}`}
                            title="Advanced Filters"
                        >
                            <ListFilter size={20} />
                        </button>

                        <button
                            onClick={handleSearch}
                            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 shadow-sm hover:shadow-glow-blue active:scale-[0.97]"
                        >
                            Search
                        </button>
                    </div>
                </div>

                {/* Advanced Filters Row */}
                {showAdvanced && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-950/40 rounded-xl border border-slate-700/30">

                        {/* Source */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium">Source</label>
                            <div className="relative">
                                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                                <select
                                    className="input-base w-full pl-9 pr-2 py-2 text-sm appearance-none"
                                    value={sourceFilter}
                                    onChange={(e) => setSourceFilter(e.target.value)}
                                >
                                    <option value="">All Sources</option>
                                    <option value="keepa">Amazon</option>
                                    <option value="promodescuentos">PromoDescuentos</option>
                                    <option value="officedepot">Office Depot</option>
                                    <option value="cyberpuerta">Cyberpuerta</option>
                                    <option value="elektra">Elektra</option>
                                    <option value="chedraui">Chedraui</option>
                                    <option value="coppel">Coppel</option>
                                    <option value="liverpool">Liverpool</option>
                                    <option value="mercadolibre">MercadoLibre</option>
                                    <option value="sephora">Sephora</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                        </div>

                        {/* Price Range */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium">Price Range</label>
                            <div className="flex gap-2">
                                <input
                                    type="number"
                                    placeholder="Min"
                                    className="input-base w-full px-3 py-2 text-sm"
                                    value={minPrice}
                                    onChange={e => setMinPrice(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                />
                                <input
                                    type="number"
                                    placeholder="Max"
                                    className="input-base w-full px-3 py-2 text-sm"
                                    value={maxPrice}
                                    onChange={e => setMaxPrice(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                />
                            </div>
                        </div>

                        {/* Sort */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium">Sort By</label>
                            <select
                                className="input-base w-full px-3 py-2 text-sm"
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                            >
                                <option value="newest">Newest First</option>
                                <option value="price_asc">Price: Low to High</option>
                                <option value="price_desc">Price: High to Low</option>
                            </select>
                        </div>

                        {/* Exclude */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={showExclude}
                                    onChange={e => setShowExclude(e.target.checked)}
                                    className="rounded border-slate-700/60 bg-slate-950 text-blue-600 focus:ring-blue-500/50"
                                />
                                Exclude Words
                            </label>
                            {showExclude ? (
                                <input
                                    type="text"
                                    placeholder="e.g. funda case"
                                    className="w-full bg-slate-950 border border-slate-700/60 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500/70 focus:ring-1 focus:ring-red-500/20 text-slate-200 placeholder-slate-600 transition-colors duration-150"
                                    value={exclude}
                                    onChange={e => setExclude(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                />
                            ) : (
                                <div className="h-[38px] flex items-center text-xs text-slate-600 italic px-2">
                                    Check to enable exclusion
                                </div>
                            )}
                        </div>

                        {/* Clear Button */}
                        <div className="col-span-1 sm:col-span-2 md:col-span-4 flex justify-end">
                            <button
                                onClick={clearFilters}
                                className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
                            >
                                <X size={12} /> Clear Filters
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div className="overflow-auto flex-1">
                <table className="w-full text-left text-sm">
                    <thead className="bg-[#080f1a] text-slate-500 sticky top-0 z-10 border-b border-slate-700/30">
                        <tr>
                            <th className="px-5 py-3.5 font-medium text-xs uppercase tracking-wider">Product Name</th>
                            <th className="px-5 py-3.5 font-medium text-xs uppercase tracking-wider">Source</th>
                            <th className="px-5 py-3.5 font-medium text-xs uppercase tracking-wider">Price</th>
                            <th className="px-5 py-3.5 font-medium text-xs uppercase tracking-wider text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                        {products.map(p => (
                            <tr key={p.id} className="hover:bg-slate-800/40 transition-colors duration-100 group">
                                <td className="px-5 py-4">
                                    <div className="font-medium text-slate-200 line-clamp-2 text-sm" title={p.name}>{p.name}</div>
                                    <div className="text-[11px] text-slate-600 mt-1 font-mono">{p.sku || 'NO-SKU'}</div>
                                </td>
                                <td className="px-5 py-4">
                                    <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium tracking-wide
                                    ${p.source === 'keepa' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                                            p.source === 'promodescuentos' ? 'bg-red-600/10 text-red-400 border-red-600/20' :
                                                p.source === 'officedepot' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                    p.source === 'cyberpuerta' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                        p.source === 'soriana' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                            p.source === 'coppel' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                                                p.source === 'liverpool' ? 'bg-pink-500/10 text-pink-400 border-pink-500/20' :
                                                                    p.source === 'mercadolibre' ? 'bg-yellow-400/10 text-yellow-500 border-yellow-400/20' :
                                                                        p.source === 'elektra' ? 'bg-purple-600/10 text-purple-400 border-purple-600/20' : 'bg-slate-700/50 text-slate-400 border-slate-600/30'}`}>
                                        {p.source || 'Unknown'}
                                    </span>
                                </td>
                                <td className="px-5 py-4 font-mono text-white tabular-nums">
                                    <div className="flex flex-col">
                                        <span>${p.current_price?.toLocaleString()}</span>
                                        {p.original_price && <span className="text-xs text-slate-500 line-through">${p.original_price?.toLocaleString()}</span>}
                                    </div>
                                </td>
                                <td className="px-5 py-4 text-right">
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                console.log('Edit anchor price clicked for product:', p.id);
                                                console.log('onUpdateAnchorPrice function:', onUpdateAnchorPrice);

                                                if (typeof onUpdateAnchorPrice !== 'function') {
                                                    alert('Edit function not available. Please refresh the page.');
                                                    return;
                                                }

                                                const defaultValue = p.original_price ?? p.current_price ?? '';
                                                const promptInput = window.prompt(`Enter new anchor price (MXN) for ${p.name}`, defaultValue);
                                                if (promptInput !== null && promptInput.trim() !== '') {
                                                    // Handle international number formats: replace commas with dots, remove currency symbols, etc.
                                                    const cleaned = promptInput.trim()
                                                        .replace(/[^\d.,]/g, '') // Keep digits, commas, dots
                                                        .replace(/,(\d{3})/g, '$1') // Remove thousand separators (commas between digits)
                                                        .replace(/,/g, '.'); // Convert decimal comma to dot

                                                    // If there are multiple dots, keep only the last one as decimal
                                                    const parts = cleaned.split('.');
                                                    let normalized = parts.length > 1
                                                        ? parts.slice(0, -1).join('') + '.' + parts[parts.length - 1]
                                                        : cleaned;

                                                    const newPrice = parseFloat(normalized);
                                                    if (!isNaN(newPrice) && newPrice > 0) {
                                                        console.log(`Updating anchor price for product ${p.id} to ${newPrice}`);
                                                        onUpdateAnchorPrice(p.id, newPrice);
                                                    } else {
                                                        alert("Invalid price format entered. Please enter a valid number (e.g., 1999.99 or 1,999.99).");
                                                    }
                                                }
                                            }}
                                            title="Edit anchor price"
                                            className="p-2 hover:bg-blue-500/10 rounded text-slate-400 hover:text-blue-400 transition-colors">
                                            <Edit2 size={16} />
                                        </button>
                                        <button
                                            onClick={() => onToggleActive(p.id, !p.is_active)}
                                            title={p.is_active ? "Unsubscribe from alerts" : "Subscribe to alerts"}
                                            className={`p-2 rounded transition-colors ${p.is_active ? 'hover:bg-yellow-500/10 text-slate-400 hover:text-yellow-500' : 'bg-red-500/10 text-red-500 hover:bg-red-500/20'}`}>
                                            {p.is_active ? <Bell size={16} /> : <BellOff size={16} />}
                                        </button>
                                        <a href={p.url} target="_blank" rel="noopener noreferrer" className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-blue-400 transition-colors">
                                            <ExternalLink size={16} />
                                        </a>
                                        <button
                                            onClick={(e) => onDelete(p.id, e)}
                                            className="p-2 hover:bg-red-500/10 rounded text-slate-400 hover:text-red-400 transition-colors">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {products.length === 0 && (
                            <tr>
                                <td colSpan="4" className="py-16 text-center">
                                    <div className="flex flex-col items-center gap-3">
                                        <Search size={32} className="opacity-15 text-slate-600" />
                                        <p className="text-slate-500 text-sm">No products found matching criteria.</p>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination Controls */}
            {pagination && pagination.pages > 1 && (
                <div className="px-5 py-3.5 border-t border-slate-700/40 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-slate-500 bg-slate-950/40">
                    <div>
                        Showing <span className="text-white font-medium">{products.length}</span> results
                        (Page {pagination.page} of {pagination.pages})
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            disabled={pagination.page <= 1}
                            onClick={() => onPageChange(pagination.page - 1)}
                            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <ChevronLeft size={16} />
                        </button>

                        <div className="flex items-center gap-1 px-2">
                            {(() => {
                                let startPage = Math.max(1, pagination.page - 2);
                                let endPage = Math.min(pagination.pages, startPage + 4);

                                if (endPage - startPage < 4) {
                                    startPage = Math.max(1, endPage - 4);
                                }

                                const pages = [];
                                for (let i = startPage; i <= endPage; i++) {
                                    if (i > 0) pages.push(i);
                                }

                                return pages.map(p => (
                                    <button
                                        key={p}
                                        onClick={() => onPageChange(p)}
                                        className={`w-8 h-8 rounded-lg text-xs font-medium transition-colors ${p === pagination.page
                                            ? 'bg-blue-600 text-white shadow-sm shadow-blue-900/30'
                                            : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                                            }`}
                                    >
                                        {p}
                                    </button>
                                ));
                            })()}
                        </div>

                        <button
                            disabled={pagination.page >= pagination.pages}
                            onClick={() => onPageChange(pagination.page + 1)}
                            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
