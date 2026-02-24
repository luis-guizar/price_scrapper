
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ExternalLink, ArrowLeft } from 'lucide-react';

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

    const sourceConfig = {
        keepa: { label: 'Amazon', color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30' },
        promodescuentos: { label: 'PromoDescuentos', color: 'text-red-400', bg: 'bg-red-600/10 border-red-600/30' },
        officedepot: { label: 'Office Depot', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30' },
        cyberpuerta: { label: 'CyberPuerta', color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/30' },
        chedraui: { label: 'Chedraui', color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30' },
        elektra: { label: 'Elektra', color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30' },
        soriana: { label: 'Soriana', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30' },
        coppel: { label: 'Coppel', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/30' },
        liverpool: { label: 'Liverpool', color: 'text-pink-400', bg: 'bg-pink-500/10 border-pink-500/30' },
        mercadolibre: { label: 'MercadoLibre', color: 'text-yellow-500', bg: 'bg-yellow-400/10 border-yellow-400/30' },
        other: { label: 'Other', color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/30' },
    };

    return (
        <div className="h-full flex flex-col p-6">
            <div className="flex items-center gap-4 mb-6">
                <button
                    onClick={onBack}
                    className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                >
                    <ArrowLeft size={20} />
                </button>
                <h2 className="text-xl font-semibold text-slate-200">Alert History</h2>
            </div>

            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden flex-1 flex flex-col">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-400">
                        <thead className="bg-slate-900/80 text-xs uppercase font-medium text-slate-500 sticky top-0 backdrop-blur-sm z-10">
                            <tr>
                                <th className="px-6 py-4">Date</th>
                                <th className="px-6 py-4">Product</th>
                                <th className="px-6 py-4">Price</th>
                                <th className="px-6 py-4">Discount</th>
                                <th className="px-6 py-4 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {loading ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-8 text-center text-slate-500">
                                        Loading history...
                                    </td>
                                </tr>
                            ) : alerts.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-8 text-center text-slate-500">
                                        No alerts sent yet.
                                    </td>
                                </tr>
                            ) : (
                                alerts.map((alert) => (
                                    <tr key={alert.id} className="hover:bg-slate-800/30 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {new Date(alert.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="text-slate-200 font-medium line-clamp-1 max-w-xs" title={alert.title}>
                                                    {alert.title || "Unknown Product"}
                                                </span>
                                                <div className="mt-1">
                                                    <span className={`text-[10px] uppercase tracking-wider inline-block px-1.5 py-0.5 rounded ${sourceConfig[alert.source]?.bg || 'bg-slate-800 text-slate-500'} ${sourceConfig[alert.source]?.color || 'text-slate-400'}`}>
                                                        {sourceConfig[alert.source]?.label || alert.source}
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
                                                <span className="text-emerald-400 font-medium bg-emerald-500/10 px-2 py-1 rounded">
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
