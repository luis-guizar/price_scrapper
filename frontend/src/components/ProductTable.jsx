import React, { useState } from 'react'
import { Search, Trash2, ExternalLink, Filter, ChevronLeft, ChevronRight } from 'lucide-react'

export default function ProductTable({ products, onDelete, onSearch, pagination, onPageChange }) {
    const [search, setSearch] = useState('')
    const [sourceFilter, setSourceFilter] = useState('')

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            onSearch(search, sourceFilter)
        }
    }

    // Trigger search when source changes? No, request says "only perform the search with both... when hitting enter".
    // So we just update state. The prompt says "It should also include a source filter and a search box, which should only perform the serch with both the category and the search as parameters when hiting enter."
    // This implies that selecting a source shouldn't trigger search immediately.
    // However, usually filters are immediate. But I will follow instructions strictly.

    return (
        <div className="bg-slate-900/50 rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4">
                <h3 className="font-semibold text-lg">All Tracked Products</h3>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                    {/* Source Filter */}
                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                        <select
                            className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-8 py-2 text-sm focus:outline-none focus:border-blue-500 appearance-none text-slate-300"
                            value={sourceFilter}
                            onChange={(e) => setSourceFilter(e.target.value)}
                        >
                            <option value="">All Sources</option>
                            <option value="mercadolibre">MercadoLibre</option>
                            <option value="walmart">Walmart</option>
                            <option value="officedepot">Office Depot</option>
                            <option value="cyberpuerta">Cyberpuerta</option>
                            <option value="amazon">Amazon</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    {/* Search Box */}
                    <div className="relative flex-1 sm:w-64">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                        <input
                            type="text"
                            placeholder="Search... (Press Enter)"
                            className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 w-full text-white"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                    </div>

                    <button
                        onClick={() => onSearch(search, sourceFilter)}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                        Search
                    </button>
                </div>
            </div>

            <div className="overflow-auto flex-1">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-950 text-slate-400 sticky top-0">
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
                                                    p.source === 'cyberpuerta' ? 'bg-purple-500/10 text-purple-500' : 'bg-slate-700 text-slate-300'}`}>
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
                                <td colSpan="4" className="p-8 text-center text-slate-500">
                                    No products found matching criteria.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination Controls */}
            {pagination && pagination.pages > 1 && (
                <div className="p-4 border-t border-slate-800 flex justify-between items-center text-sm text-slate-400 bg-slate-900/30">
                    <div>
                        Showing <span className="text-white font-medium">{products.length}</span> results
                        (Page {pagination.page} of {pagination.pages})
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            disabled={pagination.page <= 1}
                            onClick={() => onPageChange(pagination.page - 1, search, sourceFilter)}
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
                                    pages.push(i);
                                }

                                return pages.map(p => (
                                    <button
                                        key={p}
                                        onClick={() => onPageChange(p, search, sourceFilter)}
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
                            onClick={() => onPageChange(pagination.page + 1, search, sourceFilter)}
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
