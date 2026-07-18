import { useState, useEffect } from 'react'
import axios from 'axios'
import { ShoppingCart, TrendingDown, Plus, Trash2, Search, ExternalLink, Send, Menu, X, Bell, BellOff, Edit2 } from 'lucide-react'
import ProductTable from './components/ProductTable'
import TelegramModal from './components/TelegramModal'
import AlertHistory from './components/AlertHistory'
import SidebarNav from './components/SidebarNav'
import SephoraView from './components/SephoraView'
import PriceHistoryChart from './components/PriceHistoryChart'
import { getSourceBadge } from './utils/sourceConfig'

function App() {
    const [products, setProducts] = useState([])
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedProduct, setSelectedProduct] = useState(null)
    const [history, setHistory] = useState([])
    const [showAddModal, setShowAddModal] = useState(false)
    const [showTelegramModal, setShowTelegramModal] = useState(false)
    const [mobileNavOpen, setMobileNavOpen] = useState(false)
    const [viewMode, setViewMode] = useState('dashboard') // 'dashboard' | 'list' | 'alerts'
    const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0, limit: 20 })
    const [activeFilters, setActiveFilters] = useState({
        search: '',
        source: '',
        minPrice: '',
        maxPrice: '',
        sortBy: 'newest',
        exclude: ''
    })

    // Add modal state
    const [newUrl, setNewUrl] = useState('')
    const [addSource, setAddSource] = useState(null)
    const [addPreview, setAddPreview] = useState(null)
    const [addLoading, setAddLoading] = useState(false)
    const [addError, setAddError] = useState('')
    const [addStep, setAddStep] = useState('url') // 'url' | 'preview' | 'success'

    // Dashboard search state
    const [dashboardSearch, setDashboardSearch] = useState('')
    const [dashboardSourceFilter, setDashboardSourceFilter] = useState('')
    const [dashboardMinPrice, setDashboardMinPrice] = useState('')
    const [dashboardMaxPrice, setDashboardMaxPrice] = useState('')
    const [dashboardProducts, setDashboardProducts] = useState([])
    const [dashboardLoading, setDashboardLoading] = useState(false)

    useEffect(() => {
        fetchData()
    }, [])

    // Deep-link support: ?view=sephora opens the Sephora screen; ?product=<id>
    // opens straight to that product's detail pane. A friend can bookmark
    // /?view=sephora to land directly on the Sephora trends/deals screen.
    useEffect(() => {
        const params = new URLSearchParams(window.location.search)

        if (params.get('view') === 'sephora') {
            setViewMode('sephora')
        }

        const productId = params.get('product')
        if (!productId) return

        setViewMode('dashboard')
        axios.get(`/api/products/${productId}`)
            .then(res => setSelectedProduct(res.data))
            .catch(error => console.error("Error loading linked product:", error))
    }, [])

    useEffect(() => {
        if (selectedProduct) {
            fetchHistory(selectedProduct.id)
        }
    }, [selectedProduct])

    // Lock body scroll while the mobile nav drawer is open
    useEffect(() => {
        document.body.style.overflow = mobileNavOpen ? 'hidden' : ''
        return () => { document.body.style.overflow = '' }
    }, [mobileNavOpen])

    // Close the mobile nav drawer on Escape
    useEffect(() => {
        if (!mobileNavOpen) return
        const onKey = (e) => e.key === 'Escape' && setMobileNavOpen(false)
        window.addEventListener('keydown', onKey)
        return () => window.removeEventListener('keydown', onKey)
    }, [mobileNavOpen])

    // Fetch dashboard products when filters change
    useEffect(() => {
        handleDashboardSearch()
    }, [dashboardSearch, dashboardSourceFilter, dashboardMinPrice, dashboardMaxPrice])

    // Auto-detect source from URL
    useEffect(() => {
        if (!newUrl) {
            setAddSource(null)
            setAddError('')
            return
        }
        const lc = newUrl.toLowerCase()
        if (lc.includes('amazon.com.mx') || lc.includes('amzn.to')) {
            setAddSource('keepa')
        } else if (lc.includes('elektra.com') || lc.includes('elektra.mx')) {
            setAddSource('elektra')
        } else if (lc.includes('cyberpuerta.mx')) {
            setAddSource('cyberpuerta')
        } else if (lc.includes('chedraui.com.mx')) {
            setAddSource('chedraui')
        } else if (lc.includes('officedepot.com.mx')) {
            setAddSource('officedepot')
        } else if (lc.includes('coppel.com') || lc.includes('motoscoppel.mx')) {
            setAddSource('coppel')
        } else if (lc.includes('mercadolibre.com')) {
            setAddSource('mercadolibre')
        } else if (lc.includes('liverpool.com.mx')) {
            setAddSource('liverpool')
        } else if (lc.includes('sephora.com.mx')) {
            setAddSource('sephora')
        } else if (lc.includes('sears.com.mx')) {
            setAddSource('sears')
        } else if (lc.includes('costco.com.mx')) {
            setAddSource('costco')
        } else if (lc.startsWith('http')) {
            setAddSource('other')
        } else {
            setAddSource(null)
        }
    }, [newUrl])

    const fetchData = async (params = {}) => {
        setLoading(true)
        try {
            const apiParams = {
                limit: params.limit || 20,
                skip: params.skip || 0,
                search: params.search || undefined,
                source: params.source || undefined,
                min_price: params.minPrice || undefined,
                max_price: params.maxPrice || undefined,
                sort_by: params.sortBy || undefined,
                exclude: params.exclude || undefined
            }

            const [productsRes, statsRes] = await Promise.all([
                axios.get('/api/products', { params: apiParams }),
                axios.get('/api/stats')
            ])

            if (productsRes.data.data) {
                setProducts(productsRes.data.data)
                setPagination({
                    page: productsRes.data.page,
                    pages: productsRes.data.pages,
                    total: productsRes.data.total,
                    limit: productsRes.data.limit
                })
            } else {
                setProducts(productsRes.data)
            }

            setStats(statsRes.data)
        } catch (error) {
            console.error("Error fetching data:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = (filters = {}, page = 1) => {
        const newFilters = { ...activeFilters, ...filters }
        setActiveFilters(newFilters)

        const limit = pagination.limit
        const skip = (page - 1) * limit

        fetchData({
            search: newFilters.search || undefined,
            source: newFilters.source || undefined,
            minPrice: newFilters.minPrice || undefined,
            maxPrice: newFilters.maxPrice || undefined,
            sortBy: newFilters.sortBy || undefined,
            exclude: newFilters.exclude || undefined,
            limit: limit,
            skip: skip
        })
    }

    const handlePageChange = (newPage) => {
        handleSearch({}, newPage)
    }

    // Fetch dashboard products from API with search filters
    const handleDashboardSearch = async () => {
        setDashboardLoading(true)
        try {
            const apiParams = {
                limit: 1000, // Get all items for dashboard display
                skip: 0,
                min_history_count: 2,
                search: dashboardSearch || undefined,
                source: dashboardSourceFilter || undefined,
                min_price: dashboardMinPrice ? parseFloat(dashboardMinPrice) : undefined,
                max_price: dashboardMaxPrice ? parseFloat(dashboardMaxPrice) : undefined,
            }

            // Remove undefined values
            Object.keys(apiParams).forEach(key => apiParams[key] === undefined && delete apiParams[key])

            const res = await axios.get('/api/products', { params: apiParams })

            if (res.data.data) {
                setDashboardProducts(res.data.data)
            } else {
                setDashboardProducts(res.data)
            }
        } catch (error) {
            console.error("Error fetching dashboard products:", error)
            setDashboardProducts([])
        } finally {
            setDashboardLoading(false)
        }
    }

    const handleDashboardClearFilters = () => {
        setDashboardSearch('')
        setDashboardSourceFilter('')
        setDashboardMinPrice('')
        setDashboardMaxPrice('')
    }

    const fetchHistory = async (id) => {
        try {
            const res = await axios.get(`/api/products/${id}/history`)
            if (Array.isArray(res.data)) {
                const data = res.data.map(item => ({
                    ...item,
                    date: new Date(item.timestamp).toLocaleDateString() + ' ' + new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }))
                setHistory(data)
            } else {
                setHistory([])
            }
        } catch (error) {
            console.error("Error history", error)
        }
    }

    // --- New smart track handlers ---

    const handlePreview = async () => {
        if (!newUrl) return
        setAddLoading(true)
        setAddError('')
        setAddPreview(null)

        try {
            const res = await axios.post('/api/products/preview-url', { url: newUrl })
            setAddPreview(res.data)
            setAddStep('preview')
        } catch (err) {
            const msg = err.response?.data?.detail || 'Could not fetch product info. Check the URL.'
            setAddError(msg)
        } finally {
            setAddLoading(false)
        }
    }

    const handleTrackConfirm = async () => {
        setAddLoading(true)
        setAddError('')

        try {
            await axios.post('/api/products/track-url', { url: newUrl })
            setAddStep('success')
            fetchData()
            // Auto-close after a moment
            setTimeout(() => {
                closeAddModal()
            }, 1500)
        } catch (err) {
            const msg = err.response?.data?.detail || 'Error adding product.'
            setAddError(msg)
        } finally {
            setAddLoading(false)
        }
    }

    const closeAddModal = () => {
        setShowAddModal(false)
        setNewUrl('')
        setAddSource(null)
        setAddPreview(null)
        setAddLoading(false)
        setAddError('')
        setAddStep('url')
    }

    const handleDelete = async (id, e) => {
        e?.stopPropagation()
        if (!confirm("Stop tracking this item?")) return
        try {
            await axios.delete(`/api/products/${id}`)
            const limit = pagination.limit
            const skip = (pagination.page - 1) * limit

            fetchData({
                ...activeFilters,
                limit: limit,
                skip: skip
            })

            if (selectedProduct?.id === id) setSelectedProduct(null)
        } catch (e) {
            alert("Error deleting")
        }
    }

    const handleToggleActive = async (id, isActive) => {
        try {
            await axios.patch(`/api/products/${id}`, { is_active: isActive })

            // Update local state to reflect change immediately without full reload
            setProducts(prev => prev.map(p => p.id === id ? { ...p, is_active: isActive } : p))
            setDashboardProducts(prev => prev.map(p => p.id === id ? { ...p, is_active: isActive } : p))
            if (selectedProduct?.id === id) {
                setSelectedProduct(prev => ({ ...prev, is_active: isActive }))
            }
        } catch (e) {
            console.error("Error toggling active status:", e)
            alert("Error updating subscription status")
        }
    }

    const handleUpdateAnchorPrice = async (id, newPrice) => {
        try {
            await axios.patch(`/api/products/${id}`, { original_price: newPrice });
            setProducts(prev => prev.map(p => p.id === id ? { ...p, original_price: newPrice } : p));
            setDashboardProducts(prev => prev.map(p => p.id === id ? { ...p, original_price: newPrice } : p));
        } catch (e) {
            console.error("Error updating anchor price:", e);
            alert("Error updating anchor price");
        }
    };

    return (
        <div className="min-h-screen bg-[#080f1a] flex text-slate-100 font-sans overflow-x-hidden">

            {/* Sidebar (desktop/tablet) */}
            <aside className="w-64 bg-gradient-to-b from-[#0d1524] to-[#080f1a] border-r border-slate-700/40 p-6 flex flex-col hidden md:flex">
                <h1 className="text-2xl font-bold logo-shimmer mb-8 tracking-tight">
                    PriceTracker
                </h1>
                <SidebarNav
                    viewMode={viewMode}
                    setViewMode={setViewMode}
                    stats={stats}
                    onBroadcastClick={() => setShowTelegramModal(true)}
                />
            </aside>

            {/* Mobile off-canvas nav drawer */}
            <div
                className={`fixed inset-0 z-40 md:hidden ${mobileNavOpen ? '' : 'pointer-events-none'}`}
                aria-hidden={!mobileNavOpen}
            >
                <div
                    className={`absolute inset-0 bg-black/70 backdrop-blur-[2px] transition-opacity duration-300 ${mobileNavOpen ? 'opacity-100' : 'opacity-0'}`}
                    onClick={() => setMobileNavOpen(false)}
                />
                <aside
                    className={`absolute inset-y-0 left-0 w-72 max-w-[85%] bg-gradient-to-b from-[#0d1524] to-[#080f1a] border-r border-slate-700/40 p-6 flex flex-col shadow-2xl shadow-black/60 transition-transform duration-300 ease-out ${mobileNavOpen ? 'translate-x-0' : '-translate-x-full'}`}
                    style={{
                        paddingTop: 'max(1.5rem, env(safe-area-inset-top))',
                        paddingBottom: 'max(1.5rem, env(safe-area-inset-bottom))'
                    }}
                >
                    <div className="flex items-center justify-between mb-8">
                        <h1 className="text-2xl font-bold logo-shimmer tracking-tight">
                            PriceTracker
                        </h1>
                        <button
                            onClick={() => setMobileNavOpen(false)}
                            aria-label="Close menu"
                            className="p-2 -mr-2 text-slate-400 hover:text-white hover:bg-slate-800/70 rounded-lg"
                        >
                            <X size={22} />
                        </button>
                    </div>
                    <SidebarNav
                        viewMode={viewMode}
                        setViewMode={setViewMode}
                        stats={stats}
                        onBroadcastClick={() => setShowTelegramModal(true)}
                        onNavigate={() => setMobileNavOpen(false)}
                    />
                </aside>
            </div>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-4 md:p-10">

                {/* Header */}
                <header className="flex justify-between items-center mb-6 md:mb-8 gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                        <button
                            onClick={() => setMobileNavOpen(true)}
                            aria-label="Open menu"
                            className="md:hidden -ml-1.5 p-2.5 text-slate-300 hover:text-white hover:bg-slate-800/70 rounded-lg shrink-0"
                        >
                            <Menu size={22} />
                        </button>
                        <h2 className="text-xl md:text-2xl font-semibold text-slate-100 tracking-tight truncate">
                            {viewMode === 'dashboard' ? 'Overview' : viewMode === 'list' ? 'Product Inventory' : viewMode === 'sephora' ? 'Sephora' : 'Alert History'}
                        </h2>
                    </div>
                    <button
                        onClick={() => setShowAddModal(true)}
                        aria-label="Track New Item"
                        className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-3.5 sm:px-5 py-2.5 rounded-xl font-semibold transition-all duration-150 shadow-lg shadow-blue-900/40 hover:shadow-glow-blue hover:scale-[1.02] active:scale-[0.97] shrink-0">
                        <Plus size={18} />
                        <span className="hidden sm:inline">Track New Item</span>
                    </button>
                </header>

                {viewMode === 'dashboard' ? (
                    <>
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-6 md:mb-8">
                            <div className="bg-[#0d1524] p-5 md:p-6 rounded-2xl border border-slate-700/50 shadow-card hover:shadow-card-md transition-shadow duration-200 relative overflow-hidden">
                                <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-indigo-500/40 via-indigo-500/10 to-transparent" />
                                <div className="flex justify-between items-start mb-4">
                                    <div className="p-3 bg-indigo-500/15 rounded-xl text-indigo-300 shadow-sm shadow-indigo-900/20">
                                        <ShoppingCart size={24} />
                                    </div>
                                </div>
                                <h3 className="text-slate-500 text-xs font-medium uppercase tracking-wider">Tracked Products</h3>
                                <p className="text-4xl font-bold text-white mt-1 tracking-tight tabular-nums">{stats?.products_count || 0}</p>
                            </div>

                            <div
                                className="bg-[#0d1524] p-5 md:p-6 rounded-2xl border border-slate-700/50 shadow-card hover:shadow-card-md hover:border-emerald-500/20 cursor-pointer transition-all duration-200 group relative overflow-hidden"
                                onClick={() => setViewMode('alerts')}
                            >
                                <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-emerald-500/40 via-emerald-500/10 to-transparent" />
                                <div className="flex justify-between items-start mb-4">
                                    <div className="p-3 bg-emerald-500/15 rounded-xl text-emerald-300 shadow-sm shadow-emerald-900/20 group-hover:scale-110 transition-transform duration-150">
                                        <TrendingDown size={24} />
                                    </div>
                                </div>
                                <h3 className="text-slate-500 text-xs font-medium uppercase tracking-wider">Deals Found</h3>
                                <p className="text-4xl font-bold text-white mt-1 tracking-tight tabular-nums">{stats?.alerts_count || 0}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 lg:h-[600px]">

                            {/* Product List */}
                            <div className="lg:col-span-1 bg-[#0d1524] rounded-2xl border border-slate-700/50 flex flex-col overflow-hidden shadow-card">
                                <div className="p-4 border-b border-slate-700/40 flex flex-col gap-3">
                                    <div className="flex justify-between items-center">
                                        <h3 className="font-semibold text-slate-200 text-sm tracking-wide">Tracked Items</h3>
                                        <span className="text-xs bg-slate-800/80 px-2.5 py-1 rounded-full text-slate-400 font-mono tabular-nums">{dashboardProducts.length}</span>
                                    </div>

                                    {/* Search & Filter Controls */}
                                    <div className="flex gap-2 items-center">
                                        <div className="relative flex-1">
                                            <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                                            <input
                                                type="text"
                                                placeholder="Search..."
                                                className="input-base pl-7 pr-3 py-1.5 text-xs w-full"
                                                value={dashboardSearch}
                                                onChange={e => setDashboardSearch(e.target.value)}
                                                onKeyDown={e => e.key === 'Enter' && e.currentTarget.blur()}
                                            />
                                        </div>

                                        {(dashboardSearch || dashboardSourceFilter || dashboardMinPrice || dashboardMaxPrice) && (
                                            <button
                                                onClick={handleDashboardClearFilters}
                                                className="p-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-700/60 rounded-lg hover:bg-slate-800/70 transition-colors"
                                                title="Clear filters"
                                            >
                                                <X size={14} />
                                            </button>
                                        )}
                                    </div>

                                    {/* Source & Price Filters (Compact) */}
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                        <select
                                            value={dashboardSourceFilter}
                                            onChange={e => setDashboardSourceFilter(e.target.value)}
                                            className="input-base px-2 py-1 text-xs"
                                        >
                                            <option value="">All Sources</option>
                                            <option value="keepa">Amazon</option>
                                            <option value="promodescuentos">PromoDescuentos</option>
                                            <option value="officedepot">Office Depot</option>
                                            <option value="cyberpuerta">CyberPuerta</option>
                                            <option value="chedraui">Chedraui</option>
                                            <option value="elektra">Elektra</option>
                                            <option value="coppel">Coppel</option>
                                            <option value="liverpool">Liverpool</option>
                                            <option value="mercadolibre">MercadoLibre</option>
                                            <option value="sephora">Sephora</option>
                                            <option value="sears">Sears</option>
                                            <option value="costco">Costco</option>
                                            <option value="other">Other</option>
                                        </select>

                                        <input
                                            type="number"
                                            placeholder="Min $"
                                            value={dashboardMinPrice}
                                            onChange={e => setDashboardMinPrice(e.target.value)}
                                            className="input-base px-2 py-1 text-xs"
                                        />

                                        <input
                                            type="number"
                                            placeholder="Max $"
                                            value={dashboardMaxPrice}
                                            onChange={e => setDashboardMaxPrice(e.target.value)}
                                            className="input-base px-2 py-1 text-xs"
                                        />
                                    </div>
                                </div>
                                <div className="overflow-y-auto flex-1 p-2 space-y-2 max-h-[50vh] lg:max-h-none">
                                    {dashboardLoading ? (
                                        <div className="h-full flex flex-col items-center justify-center text-slate-600 py-8">
                                            <div className="animate-spin mb-2">
                                                <Search size={32} className="opacity-30" />
                                            </div>
                                            <p className="text-sm text-slate-500">Searching...</p>
                                        </div>
                                    ) : dashboardProducts.length > 0 ? (
                                        dashboardProducts.map(p => (
                                            <div
                                                key={p.id}
                                                onClick={() => setSelectedProduct(p)}
                                                className={`group p-3 rounded-xl border cursor-pointer transition-all duration-150 hover:bg-slate-800/60 ${selectedProduct?.id === p.id ? 'bg-slate-800/80 border-blue-500/40 shadow-sm shadow-blue-900/20' : 'border-transparent hover:border-slate-700/40'}`}
                                            >
                                                <div className="flex justify-between items-start">
                                                    <h4 className="font-medium text-sm line-clamp-2 leading-snug mb-1.5 text-slate-200">{p.name || "Loading..."}</h4>
                                                    <div className="flex gap-1">
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                console.log('Edit anchor price clicked for product:', p.id);
                                                                console.log('handleUpdateAnchorPrice function:', handleUpdateAnchorPrice);

                                                                if (typeof handleUpdateAnchorPrice !== 'function') {
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
                                                                        handleUpdateAnchorPrice(p.id, newPrice);
                                                                    } else {
                                                                        alert("Invalid price format entered. Please enter a valid number (e.g., 1999.99 or 1,999.99).");
                                                                    }
                                                                }
                                                            }}
                                                            title="Edit anchor price"
                                                            className="p-1 rounded transition-all text-slate-500 hover:text-blue-500 hover:bg-blue-500/10">
                                                            <Edit2 size={14} />
                                                        </button>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); handleToggleActive(p.id, !p.is_active) }}
                                                            title={p.is_active ? "Unsubscribe from alerts" : "Subscribe to alerts"}
                                                            className={`p-1 rounded transition-all ${p.is_active ? 'text-slate-500 hover:text-yellow-500 hover:bg-yellow-500/10' : 'text-red-500 bg-red-500/10 hover:bg-red-500/20'}`}>
                                                            {p.is_active ? <Bell size={14} /> : <BellOff size={14} />}
                                                        </button>
                                                        <button
                                                            onClick={(e) => handleDelete(p.id, e)}
                                                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 hover:text-red-400 rounded text-slate-500 transition-all">
                                                            <Trash2 size={14} />
                                                        </button>
                                                    </div>
                                                </div>
                                                <div className="flex justify-between items-end mt-2">
                                                    <div>
                                                        <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider block mb-1">Current Price</span>
                                                        <div className="flex flex-col">
                                                            <span className="text-lg font-bold text-white tabular-nums">${p.current_price?.toLocaleString()}</span>
                                                            {p.original_price && <span className="text-[10px] text-slate-500 line-through">${p.original_price?.toLocaleString()}</span>}
                                                        </div>
                                                    </div>
                                                    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium tracking-wide ${getSourceBadge(p.source).bg}`}>
                                                        {getSourceBadge(p.source).label}
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-slate-600 py-8">
                                            <Search size={36} className="mb-3 opacity-30" />
                                            <p className="text-sm text-slate-500 font-medium">No items match your filters</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Chart Area */}
                            <div className="lg:col-span-2 bg-[#0d1524] rounded-2xl border border-slate-700/50 p-6 flex flex-col shadow-card">
                                {selectedProduct ? (
                                    <>
                                        <div className="flex justify-between items-start mb-6">
                                            <div>
                                                <h2 className="text-xl font-bold text-slate-100 tracking-tight">{selectedProduct.name}</h2>
                                                <a href={selectedProduct.url} target="_blank" rel="noreferrer" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 mt-1">
                                                    View on Store <ExternalLink size={12} />
                                                </a>
                                            </div>
                                            <div className="flex items-start gap-4">
                                                <button
                                                    onClick={() => handleToggleActive(selectedProduct.id, !selectedProduct.is_active)}
                                                    title={selectedProduct.is_active ? "Disable alerts for this product" : "Enable alerts for this product"}
                                                    className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold border transition-colors ${selectedProduct.is_active ? 'text-slate-300 border-slate-600/50 hover:bg-yellow-500/10 hover:text-yellow-400 hover:border-yellow-500/30' : 'text-red-400 bg-red-500/10 border-red-500/30'}`}>
                                                    {selectedProduct.is_active ? <Bell size={14} /> : <BellOff size={14} />}
                                                    {selectedProduct.is_active ? 'Disable Alerts' : 'Alerts Disabled'}
                                                </button>
                                                <div className="text-right">
                                                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-0.5">Latest Check</p>
                                                    <p className="font-mono text-xs text-slate-400 tabular-nums">{new Date(selectedProduct.last_checked).toLocaleString()}</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex-1 w-full min-h-[300px] h-[320px] lg:h-auto">
                                            <PriceHistoryChart data={history} />
                                        </div>
                                    </>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-1">
                                        <Search size={48} className="mb-3 opacity-25" />
                                        <p className="text-sm font-medium text-slate-500">Select a product to view price history</p>
                                        <p className="text-xs text-slate-600 mt-1">Click any item in the list on the left</p>
                                    </div>
                                )}
                            </div>

                        </div>
                    </>
                ) : viewMode === 'list' ? (
                    // Product List View
                    <div className="h-auto lg:h-[calc(100vh-11rem)]">
                        <ProductTable
                            products={products}
                            onDelete={handleDelete}
                            onToggleActive={handleToggleActive}
                            onUpdateAnchorPrice={handleUpdateAnchorPrice}
                            onSearch={handleSearch}
                            activeFilters={activeFilters}
                            pagination={pagination}
                            onPageChange={handlePageChange}
                        />
                    </div>
                ) : viewMode === 'sephora' ? (
                    // Sephora Trends & Deals View
                    <SephoraView />
                ) : (
                    // Alert History View
                    <div className="h-auto lg:h-[calc(100vh-11rem)]">
                        <AlertHistory onBack={() => setViewMode('dashboard')} />
                    </div>
                )}

                {/* ===== SMART ADD MODAL ===== */}
                {showAddModal && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-[2px] flex items-center justify-center z-50 p-4" onClick={closeAddModal}>
                        <div
                            className="bg-[#0d1524] border border-slate-600/40 rounded-2xl w-full max-w-lg shadow-2xl shadow-black/60 overflow-hidden"
                            onClick={e => e.stopPropagation()}
                            style={{ animation: 'modalSlideIn 0.25s ease-out' }}
                        >
                            {/* Modal Header */}
                            <div className="px-6 pt-6 pb-4 border-b border-slate-700/40">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-semibold text-slate-100 tracking-tight">Track New Product</h3>
                                        <p className="text-xs text-slate-500 mt-1">Paste a product URL to start tracking its price</p>
                                    </div>
                                    <button
                                        onClick={closeAddModal}
                                        className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                                    >×</button>
                                </div>
                            </div>

                            {/* Modal Body */}
                            <div className="p-6">

                                {/* Step 1: URL Input */}
                                {addStep === 'url' && (
                                    <div>
                                        {/* URL Input with source badge */}
                                        <label className="block text-sm font-medium text-slate-300 mb-2">Product URL</label>
                                        <div className="relative">
                                            <input
                                                type="url"
                                                required
                                                autoFocus
                                                placeholder="https://articulo.mercadolibre.com.mx/MLM-..."
                                                className="w-full input-base rounded-xl p-3.5 pr-12"
                                                value={newUrl}
                                                onChange={e => { setNewUrl(e.target.value); setAddError('') }}
                                                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handlePreview() } }}
                                            />
                                            {addSource && (
                                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                                    <span className="text-lg">{getSourceBadge(addSource).icon}</span>
                                                </div>
                                            )}
                                        </div>

                                        {/* Source detection badge */}
                                        {addSource && (
                                            <div className="mt-3 flex items-center gap-2" style={{ animation: 'fadeIn 0.2s ease-out' }}>
                                                <span className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full border ${getSourceBadge(addSource).bg}`}>
                                                    {getSourceBadge(addSource).icon} {getSourceBadge(addSource).label}
                                                </span>
                                                {addSource === 'mercadolibre' && (
                                                    <span className="text-xs text-emerald-500 flex items-center gap-1">
                                                        ✓ Auto-fill supported
                                                    </span>
                                                )}
                                            </div>
                                        )}

                                        {/* Supported sources info */}
                                        <div className="mt-4 p-3.5 bg-slate-950/50 rounded-xl border border-slate-700/30">
                                            <p className="text-xs font-medium text-slate-400 mb-2">Supported sources with auto-fill:</p>
                                            <div className="flex flex-wrap gap-2">
                                                <span className="text-xs bg-red-500/10 text-red-500 border border-red-500/20 px-2 py-0.5 rounded-md">🖨️ Office Depot</span>
                                                <span className="text-xs bg-green-500/10 text-green-500 border border-green-500/20 px-2 py-0.5 rounded-md">💻 CyberPuerta</span>
                                                <span className="text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded-md">⚡ Elektra</span>
                                                <span className="text-xs bg-orange-500/10 text-orange-400 border border-orange-500/20 px-2 py-0.5 rounded-md">🏬 Chedraui</span>
                                                <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-md">🔵 Coppel</span>
                                                <span className="text-xs bg-pink-500/10 text-pink-400 border border-pink-500/20 px-2 py-0.5 rounded-md">💗 Liverpool</span>
                                                <span className="text-xs bg-yellow-400/10 text-yellow-500 border border-yellow-400/20 px-2 py-0.5 rounded-md">🤝 MercadoLibre</span>
                                                <span className="text-xs bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded-md">🏪 Sears</span>
                                                <span className="text-xs bg-blue-600/10 text-blue-400 border border-blue-600/20 px-2 py-0.5 rounded-md">📦 Costco</span>
                                            </div>
                                        </div>

                                        {/* Error */}
                                        {addError && (
                                            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400" style={{ animation: 'fadeIn 0.2s ease-out' }}>
                                                ⚠️ {addError}
                                            </div>
                                        )}

                                        {/* Actions */}
                                        <div className="flex justify-end gap-3 mt-6">
                                            <button
                                                type="button"
                                                onClick={closeAddModal}
                                                className="px-4 py-2.5 text-slate-400 hover:text-white transition-colors rounded-lg"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={handlePreview}
                                                disabled={!newUrl || addLoading}
                                                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2"
                                            >
                                                {addLoading ? (
                                                    <>
                                                        <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                                        Fetching...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Search size={16} />
                                                        Fetch Product
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Step 2: Preview */}
                                {addStep === 'preview' && addPreview && (
                                    <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                                        {/* Product Preview Card */}
                                        <div className="bg-slate-800/60 rounded-xl border border-slate-700/60 p-4">
                                            <div className="flex gap-4">
                                                {/* Thumbnail */}
                                                {addPreview.thumbnail && (
                                                    <div className="w-20 h-20 flex-shrink-0 rounded-lg bg-white/5 border border-slate-700/50 overflow-hidden flex items-center justify-center">
                                                        <img
                                                            src={addPreview.thumbnail}
                                                            alt=""
                                                            className="w-full h-full object-contain"
                                                            onError={e => { e.target.style.display = 'none' }}
                                                        />
                                                    </div>
                                                )}
                                                {/* Info */}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <h4 className="font-semibold text-white text-sm leading-snug line-clamp-2">
                                                            {addPreview.name || 'Unknown Product'}
                                                        </h4>
                                                        <span className={`flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full border ${getSourceBadge(addPreview.source).bg}`}>
                                                            {getSourceBadge(addPreview.source).icon} {getSourceBadge(addPreview.source).label}
                                                        </span>
                                                    </div>

                                                    {addPreview.price != null && (
                                                        <div className="mt-2">
                                                            <span className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">
                                                                ${addPreview.price?.toLocaleString()}
                                                            </span>
                                                            <span className="text-xs text-slate-500 ml-1">{addPreview.currency}</span>
                                                        </div>
                                                    )}

                                                    {addPreview.sku && (
                                                        <p className="text-xs text-slate-500 mt-1 font-mono">{addPreview.sku}</p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Error */}
                                        {addError && (
                                            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                                                ⚠️ {addError}
                                            </div>
                                        )}

                                        {/* Actions */}
                                        <div className="flex justify-between mt-6">
                                            <button
                                                onClick={() => { setAddStep('url'); setAddPreview(null); setAddError('') }}
                                                className="px-4 py-2.5 text-slate-400 hover:text-white transition-colors rounded-lg flex items-center gap-1"
                                            >
                                                ← Back
                                            </button>
                                            <button
                                                onClick={handleTrackConfirm}
                                                disabled={addLoading}
                                                className="bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 text-white px-6 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-emerald-900/20"
                                            >
                                                {addLoading ? (
                                                    <>
                                                        <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                                        Adding...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Plus size={16} />
                                                        Start Tracking
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Step 3: Success */}
                                {addStep === 'success' && (
                                    <div className="text-center py-6" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                                        <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/30 shadow-lg shadow-emerald-900/20">
                                            <span className="text-3xl text-emerald-400">✓</span>
                                        </div>
                                        <h4 className="text-lg font-semibold text-emerald-300 tracking-tight">Product Added!</h4>
                                        <p className="text-sm text-slate-500 mt-1">Price tracking has started</p>
                                    </div>
                                )}

                            </div>
                        </div>
                    </div>
                )}

                <TelegramModal
                    isOpen={showTelegramModal}
                    onClose={() => setShowTelegramModal(false)}
                />

            </main>
        </div>
    )
}

export default App
