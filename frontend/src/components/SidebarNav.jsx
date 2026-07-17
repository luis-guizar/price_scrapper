import { LayoutDashboard, List, Activity, Send, TrendingDown } from 'lucide-react'

export default function SidebarNav({ viewMode, setViewMode, stats, onBroadcastClick, onNavigate }) {
    const go = (mode) => {
        setViewMode(mode)
        onNavigate?.()
    }

    return (
        <>
            <nav className="space-y-2 flex-1">
                <button
                    onClick={() => go('dashboard')}
                    className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl font-medium border transition-colors ${viewMode === 'dashboard' ? 'bg-blue-600/15 text-blue-300 border-blue-500/30 shadow-sm shadow-blue-900/20' : 'text-slate-400 border-transparent hover:bg-slate-800/70 hover:text-slate-200'}`}>
                    <LayoutDashboard size={20} />
                    Dashboard
                </button>
                <button
                    onClick={() => go('list')}
                    className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl font-medium border transition-colors ${viewMode === 'list' ? 'bg-blue-600/15 text-blue-300 border-blue-500/30 shadow-sm shadow-blue-900/20' : 'text-slate-400 border-transparent hover:bg-slate-800/70 hover:text-slate-200'}`}>
                    <List size={20} />
                    All Products
                </button>
            </nav>

            <div className="space-y-4">
                <a
                    href="/queues/"
                    target="_blank"
                    rel="noreferrer"
                    onClick={() => onNavigate?.()}
                    className="flex items-center gap-3 w-full px-4 py-3 text-slate-400 border border-transparent rounded-xl font-medium hover:bg-slate-800/70 hover:text-slate-200 transition-colors duration-150">
                    <Activity size={20} />
                    Queue Monitor
                </a>
                <button
                    onClick={() => { onBroadcastClick(); onNavigate?.() }}
                    className="flex items-center gap-3 w-full px-4 py-3 bg-slate-800/80 text-slate-200 rounded-xl font-medium border border-slate-600/50 hover:bg-slate-700/80 hover:border-slate-500/50 transition-all duration-150 shadow-sm">
                    <Send size={18} />
                    Broadcast Update
                </button>

                <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-700/50">
                    <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2.5">Service Status</h3>
                    <div className="flex items-center gap-2 text-sm text-green-400">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        API Online
                    </div>
                </div>

                <button
                    onClick={() => go('alerts')}
                    className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl font-medium border transition-colors ${viewMode === 'alerts' ? 'bg-blue-600/15 text-blue-300 border-blue-500/30 shadow-sm shadow-blue-900/20' : 'text-slate-400 border-transparent hover:bg-slate-800/70 hover:text-slate-200'}`}>
                    <div className="relative">
                        <TrendingDown size={20} />
                        {stats?.alerts_count > 0 && <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>}
                    </div>
                    Alert History
                </button>
            </div>
        </>
    )
}
