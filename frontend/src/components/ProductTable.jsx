import React, { useState } from 'react'
import { Search, Trash2, ExternalLink } from 'lucide-react'

export default function ProductTable({ products, onDelete }) {
    const [search, setSearch] = useState('')

    const filtered = products.filter(p =>
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        (p.sku && p.sku.toLowerCase().includes(search.toLowerCase()))
    )

    return (
        <div className="bg-slate-900/50 rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center gap-4">
                <h3 className="font-semibold text-lg">All Tracked Products</h3>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search products..."
                        className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 w-64"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
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
                        {filtered.map(p => (
                            <tr key={p.id} className="hover:bg-slate-800/50 transition-colors">
                                <td className="p-4">
                                    <div className="font-medium text-slate-200 line-clamp-2" title={p.name}>{p.name}</div>
                                    <div className="text-xs text-slate-500 mt-1 font-mono">{p.sku || 'NO-SKU'}</div>
                                </td>
                                <td className="p-4">
                                    <span className={`px-2 py-1 rounded text-xs uppercase font-bold tracking-wider 
                                    ${p.source === 'mercadolibre' ? 'bg-yellow-500/10 text-yellow-500' :
                                            p.source === 'walmart' ? 'bg-blue-500/10 text-blue-500' :
                                                p.source === 'officedepot' ? 'bg-red-500/10 text-red-500' : 'bg-slate-700 text-slate-300'}`}>
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
                        {filtered.length === 0 && (
                            <tr>
                                <td colSpan="4" className="p-8 text-center text-slate-500">
                                    No products found matching "{search}"
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
