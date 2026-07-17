
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ExternalLink, ArrowLeft } from 'lucide-react';
import { getSourceBadge } from '../utils/sourceConfig';

function AlertCard({ alert }) {
    const badge = getSourceBadge(alert.source);
    return (
        <div className="p-4">
            <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                    <span className="text-slate-200 font-medium text-sm line-clamp-2 block" title={alert.title}>
                        {alert.title || 'Unknown Product'}
                    </span>
                    <div className="mt-1.5">
                        <span className={`text-[10px] font-medium tracking-wide inline-flex items-center px-2 py-0.5 rounded-full border ${badge.bg}`}>
                            {badge.label}
                        </span>
                    </div>
                </div>
                {alert.change_pct ? (
                    <span className="shrink-0 text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full text-xs">
                        -{alert.change_pct}%
                    </span>
                ) : null}
            </div>

            <div className="flex items-end justify-between mt-3">
                <div className="font-mono">
                    <span className="text-white font-bold">${alert.price?.toLocaleString()}</span>
                    {alert.previous_price && (
                        <span className="text-xs text-slate-500 line-through ml-2">${alert.previous_price?.toLocaleString()}</span>
                    )}
                </div>
                <span className="text-[11px] text-slate-500 text-right shrink-0">
                    {new Date(alert.created_at).toLocaleDateString()}<br />
                    {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>

            {alert.url && (
                <a
                    href={alert.url} target="_blank" rel="noreferrer"
                    className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-center gap-1.5 h-11 text-blue-400 text-sm font-medium active:bg-blue-500/10"
                >
                    View Product <ExternalLink size={14} />
                </a>
            )}
        </div>
    );
}

const AlertHistory = ({ onBack }) => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [pagination, setPagination] = useState({ page: 1, limit: 50, hasMore: true });

    useEffect(() => {
        const fetchAlerts = async () => {
            setLoading(true);
            try {
                const res = await axios.get('/api/alerts', {
                    params: {
                        limit: pagination.limit,
                        skip: (pagination.page - 1) * pagination.limit
                    }
                });
                setAlerts(res.data);
            } catch (error) {
                console.error("Error fetching alerts:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchAlerts();
    }, [pagination.page, pagination.limit]);

    return (
        <div className="h-full flex flex-col px-2 py-4">
            <div className="flex items-center gap-4 mb-6">
                <button
                    onClick={onBack}
                    className="p-2 hover:bg-slate-800/70 rounded-lg text-slate-500 hover:text-slate-200 transition-colors duration-150"
                >
                    <ArrowLeft size={20} />
                </button>
                <h2 className="text-xl font-semibold text-slate-100 tracking-tight">Alert History</h2>
            </div>

            <div className="bg-[#0d1524] rounded-2xl border border-slate-700/50 overflow-hidden flex-1 flex flex-col shadow-card">

                {/* Mobile: card list */}
                <div className="md:hidden overflow-y-auto flex-1 divide-y divide-slate-800/50">
                    {loading ? (
                        <div className="px-6 py-16 text-center text-slate-600 text-sm">Loading history...</div>
                    ) : alerts.length === 0 ? (
                        <div className="px-6 py-16 text-center text-slate-600 text-sm">No alerts sent yet.</div>
                    ) : (
                        alerts.map(alert => <AlertCard key={alert.id} alert={alert} />)
                    )}
                </div>

                {/* Desktop/tablet: table */}
                <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-400">
                        <thead className="bg-[#080f1a] text-xs uppercase font-medium text-slate-500 tracking-wider sticky top-0 z-10 border-b border-slate-700/30">
                            <tr>
                                <th className="px-6 py-3.5">Date</th>
                                <th className="px-6 py-3.5">Product</th>
                                <th className="px-6 py-3.5">Price</th>
                                <th className="px-6 py-3.5">Discount</th>
                                <th className="px-6 py-3.5 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {loading ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-16 text-center text-slate-600 text-sm">
                                        Loading history...
                                    </td>
                                </tr>
                            ) : alerts.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-16 text-center text-slate-600 text-sm">
                                        No alerts sent yet.
                                    </td>
                                </tr>
                            ) : (
                                alerts.map((alert) => (
                                    <tr key={alert.id} className="hover:bg-slate-800/25 transition-colors duration-100">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {new Date(alert.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="text-slate-200 font-medium line-clamp-1 max-w-xs" title={alert.title}>
                                                    {alert.title || "Unknown Product"}
                                                </span>
                                                <div className="mt-1">
                                                    <span className={`text-[10px] font-medium tracking-wide inline-flex items-center px-2 py-0.5 rounded-full border ${getSourceBadge(alert.source).bg}`}>
                                                        {getSourceBadge(alert.source).label}
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex flex-col">
                                                <span className="text-white font-bold">${alert.price?.toLocaleString()}</span>
                                                {alert.previous_price && (
                                                    <span className="text-xs text-slate-500 line-through">
                                                        ${alert.previous_price?.toLocaleString()}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            {alert.change_pct ? (
                                                <span className="text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full text-xs">
                                                    -{alert.change_pct}%
                                                </span>
                                            ) : (
                                                <span className="text-slate-600">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {alert.url && (
                                                <a
                                                    href={alert.url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline"
                                                >
                                                    View <ExternalLink size={14} />
                                                </a>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AlertHistory;
