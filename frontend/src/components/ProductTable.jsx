import React, { useState, useEffect } from 'react'
import { Search, Trash2, ExternalLink, Filter, ChevronLeft, ChevronRight, X, ListFilter } from 'lucide-react'

export default function ProductTable({ products, onDelete, onSearch, pagination, onPageChange, activeFilters }) {
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
        <div className="bg-slate-900/50 rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden">

            {/* Toolbar */}
            <div className="p-4 border-b border-slate-800 flex flex-col gap-4">

                {/* Top Row: Search & Main Actions */}
                <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                    <h3 className="font-semibold text-lg whitespace-nowrap hidden md:block">All Tracked Products</h3>

                    <div className="flex items-center gap-2 w-full">
                        {/* Search Box */}
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                            <input
                                type="text"
                                placeholder="Search products..."
                                className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 w-full text-white"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>

                        <button
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className={`p-2 rounded-lg border transition-colors ${showAdvanced ? 'bg-blue-600/10 border-blue-600 text-blue-400' : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'}`}
                            title="Advanced Filters"
                        >
                            <ListFilter size={20} />
                        </button>

                        <button
                            onClick={handleSearch}
                            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                            Search
                        </button>
                    </div>
                </div>

                {/* Advanced Filters Row */}
                {showAdvanced && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-950/50 rounded-xl border border-slate-800/50">

                        {/* Source */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium">Source</label>
                            <div className="relative">
                                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                                <select
                                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-2 py-2 text-sm focus:outline-none focus:border-blue-500 appearance-none text-slate-300"
                                    value={sourceFilter}
                                    onChange={(e) => setSourceFilter(e.target.value)}
                                >
                                    <option value="">All Sources</option>
                                    <option value="mercadolibre">MercadoLibre</option>
                                    <option value="walmart">Walmart</option>
                                    <option value="officedepot">Office Depot</option>
                                    <option value="cyberpuerta">Cyberpuerta</option>
                                    <option value="elektra">Elektra</option>
                                    <option value="amazon">Amazon</option>
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
                                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 text-white"
                                    value={minPrice}
                                    onChange={e => setMinPrice(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                />
                                <input
                                    type="number"
                                    placeholder="Max"
                                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 text-white"
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
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 text-slate-300"
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
                                    className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500"
                                />
                                Exclude Words
                            </label>
                            {showExclude ? (
                                <input
                                    type="text"
                                    placeholder="e.g. funda case"
                                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500 text-white placeholder-slate-600"
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
                    <thead className="bg-slate-950 text-slate-400 sticky top-0 z-10">
                        <tr>
                            <th className="p-4 font-medium">Product Name</th>
                            <th className="p-4 font-medium">Source</th>
                            <th className="p-4 font-medium">Price</th>
                            <th className="p-4 font-medium text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {products.map(p => (
                            <tr key={p.id} className="hover:bg-slate-800/50 transition-colors">
                                <td className="p-4">
                                    <div className="font-medium text-slate-200 line-clamp-2" title={p.name}>{p.name}</div>
                                    <div className="text-xs text-slate-500 mt-1 font-mono">{p.sku || 'NO-SKU'}</div>
                                </td>
                                <td className="p-4">
                                    <span className={`px-2 py-1 rounded text-xs uppercase font-bold tracking-wider 
                                    ${p.source === 'mercadolibre' ? 'bg-yellow-500/10 text-yellow-500' :
                                            p.source === 'walmart' ? 'bg-blue-500/10 text-blue-500' :
                                                p.source === 'officedepot' ? 'bg-red-500/10 text-red-500' :
                                                    p.source === 'cyberpuerta' ? 'bg-purple-500/10 text-purple-500' :
                                                        p.source === 'elektra' ? 'bg-red-600/10 text-red-600' : 'bg-slate-700 text-slate-300'}`}>
                                        {p.source || 'Unknown'}
                                    </span>
                                </td>
                                <td className="p-4 font-mono text-white">
                                    ${p.current_price?.toLocaleString()}
                                </td>
                                <td className="p-4 text-right">
                                    <div className="flex justify-end gap-2">
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
                                <td colSpan="4" className="p-12 text-center text-slate-500">
                                    <div className="flex flex-col items-center gap-2">
                                        <Search size={32} className="opacity-20" />
                                        <p>No products found matching criteria.</p>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination Controls */}
            {pagination && pagination.pages > 1 && (
                <div className="p-4 border-t border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-slate-400 bg-slate-900/30">
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
                                            ? 'bg-blue-600 text-white'
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
