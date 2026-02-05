import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { LayoutDashboard, ShoppingCart, TrendingDown, Plus, Trash2, Search, ExternalLink } from 'lucide-react'

function App() {
    const [products, setProducts] = useState([])
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedProduct, setSelectedProduct] = useState(null)
    const [history, setHistory] = useState([])
    const [showAddModal, setShowAddModal] = useState(false)
    const [newUrl, setNewUrl] = useState('')

    useEffect(() => {
        fetchData()
    }, [])

    useEffect(() => {
        if (selectedProduct) {
            fetchHistory(selectedProduct.id)
        }
    }, [selectedProduct])

    const fetchData = async () => {
        try {
            const [productsRes, statsRes] = await Promise.all([
                axios.get('/api/products'),
                axios.get('/api/stats')
            ])
            setProducts(productsRes.data)
            setStats(statsRes.data)
            setLoading(false)
        } catch (error) {
            console.error("Error fetching data:", error)
            setLoading(false)
        }
    }

    const fetchHistory = async (id) => {
        try {
            const res = await axios.get(`/api/products/${id}/history`)
            const data = res.data.map(item => ({
                ...item,
                date: new Date(item.timestamp).toLocaleDateString() + ' ' + new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }))
            setHistory(data)
        } catch (error) {
            console.error("Error history", error)
        }
    }

    const handleAddProduct = async (e) => {
        e.preventDefault()
        try {
            await axios.post('/api/products', { name: "New Product", url: newUrl })
            setNewUrl('')
            setShowAddModal(false)
            fetchData()
        } catch (error) {
            alert("Error adding product")
        }
    }

    const handleDelete = async (id, e) => {
        e.stopPropagation()
        if (!confirm("Stop tracking this item?")) return
        try {
            await axios.delete(`/api/products/${id}`)
            fetchData()
            if (selectedProduct?.id === id) setSelectedProduct(null)
        } catch (e) {
            alert("Error deleting")
        }
    }

    return (
        <div className="min-h-screen bg-slate-950 flex text-slate-100 font-sans">

            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col hidden md:flex">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-8">
                    PriceTracker
                </h1>

                <nav className="space-y-2 flex-1">
                    <button className="flex items-center gap-3 w-full px-4 py-3 bg-blue-600/10 text-blue-400 rounded-xl font-medium border border-blue-600/20">
                        <LayoutDashboard size={20} />
                        Dashboard
                    </button>
                </nav>

                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase mb-2">Service Status</h3>
                    <div className="flex items-center gap-2 text-sm text-green-400">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        API Online
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-4 md:p-8">

                {/* Header (Mobile optimized) */}
                <header className="flex justify-between items-center mb-8">
                    <h2 className="text-xl font-semibold text-slate-200">Overview</h2>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg shadow-blue-900/20">
                        <Plus size={18} />
                        Track New Item
                    </button>
                </header>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 backdrop-blur-sm">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
                                <ShoppingCart size={24} />
                            </div>
                        </div>
                        <h3 className="text-slate-400 text-sm font-medium">Tracked Products</h3>
                        <p className="text-3xl font-bold text-white mt-1">{stats?.products_count || 0}</p>
                    </div>

                    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 backdrop-blur-sm">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                                <TrendingDown size={24} />
                            </div>
                        </div>
                        <h3 className="text-slate-400 text-sm font-medium">Deals Found</h3>
                        <p className="text-3xl font-bold text-white mt-1">--</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[600px]">

                    {/* Product List */}
                    <div className="lg:col-span-1 bg-slate-900/50 rounded-2xl border border-slate-800 flex flex-col overflow-hidden">
                        <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                            <h3 className="font-semibold">Tracked Items</h3>
                            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{products.length}</span>
                        </div>
                        <div className="overflow-y-auto flex-1 p-2 space-y-2">
                            {products.map(p => (
                                <div
                                    key={p.id}
                                    onClick={() => setSelectedProduct(p)}
                                    className={`group p-4 rounded-xl border cursor-pointer transition-all hover:bg-slate-800 ${selectedProduct?.id === p.id ? 'bg-slate-800 border-blue-500/50' : 'bg-transparent border-transparent'}`}
                                >
                                    <div className="flex justify-between items-start">
                                        <h4 className="font-medium text-sm line-clamp-2 leading-snug mb-2">{p.name || "Loading..."}</h4>
                                        <button
                                            onClick={(e) => handleDelete(p.id, e)}
                                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 hover:text-red-400 rounded text-slate-500 transition-all">
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                    <div className="flex justify-between items-end mt-2">
                                        <div>
                                            <span className="text-xs text-slate-500 block mb-1">Current Price</span>
                                            <span className="text-lg font-bold text-white">${p.current_price?.toLocaleString()}</span>
                                        </div>
                                        {p.sku && <span className="text-[10px] text-slate-600 bg-slate-900 px-1.5 py-0.5 rounded uppercase tracking-wider">{p.sku.startsWith('MLM') ? 'MercadoLibre' : 'Other'}</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Chart Area */}
                    <div className="lg:col-span-2 bg-slate-900/50 rounded-2xl border border-slate-800 p-6 flex flex-col">
                        {selectedProduct ? (
                            <>
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <h2 className="text-xl font-bold">{selectedProduct.name}</h2>
                                        <a href={selectedProduct.url} target="_blank" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 mt-1">
                                            View on Store <ExternalLink size={12} />
                                        </a>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm text-slate-400">Latest Check</p>
                                        <p className="font-mono text-xs text-slate-500">{new Date(selectedProduct.last_checked).toLocaleString()}</p>
                                    </div>
                                </div>

                                <div className="flex-1 w-full min-h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={history}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                            <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickCount={5} />
                                            <YAxis stroke="#94a3b8" fontSize={12} domain={['auto', 'auto']} tickFormatter={(val) => `$${val}`} />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                                itemStyle={{ color: '#60a5fa' }}
                                            />
                                            <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-slate-500">
                                <Search size={48} className="mb-4 opacity-50" />
                                <p>Select a product to view price history</p>
                            </div>
                        )}
                    </div>

                </div>

                {/* Modal */}
                {showAddModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
                            <h3 className="text-xl font-bold mb-4">Track New Product</h3>
                            <form onSubmit={handleAddProduct}>
                                <label className="block text-sm text-slate-400 mb-2">Product URL</label>
                                <input
                                    type="url"
                                    required
                                    placeholder="https://articulo.mercadolibre.com.mx/..."
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500 transition-colors mb-6"
                                    value={newUrl}
                                    onChange={e => setNewUrl(e.target.value)}
                                />
                                <div className="flex justify-end gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setShowAddModal(false)}
                                        className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium"
                                    >
                                        Start Tracking
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

            </main>
        </div>
    )
}

export default App
