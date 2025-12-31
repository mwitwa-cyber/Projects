import { useState, useEffect } from 'react';
import { Activity, DollarSign, Loader2, Download } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { cn } from '../lib/utils';




const mockData = [
    { name: '9:00', value: 400 },
    { name: '10:00', value: 300 },
    { name: '11:00', value: 450 },
    { name: '12:00', value: 470 },
    { name: '13:00', value: 400 },
    { name: '14:00', value: 300 },
    { name: '15:00', value: 400 },
];

const TickerCard = ({ ticker, name, price, change, sector, history, onClick }: { ticker: string, name: string, price: number, change: number, sector: string, history: any[], onClick: () => void }) => (
    <div
        onClick={onClick}
        className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-4 shadow-xl hover:scale-105 transition-transform duration-300 cursor-pointer group"
    >
        <div className="flex justify-between items-start mb-2">
            <div>
                <h3 className="text-xl font-bold text-white group-hover:text-brand-primary transition-colors">{ticker}</h3>
                <p className="text-xs text-brand-primary/80 truncate w-32">{name}</p>
                <div className="mt-1">
                    <span className="text-[10px] uppercase tracking-wider bg-white/5 px-1.5 py-0.5 rounded text-slate-400">{sector}</span>
                </div>
            </div>
            <span className={cn("px-2 py-1 rounded-full text-xs font-medium", change >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400")}>
                {change > 0 ? "+" : ""}{change.toFixed(2)}%
            </span>
        </div>

        <div className="flex items-baseline gap-2 mt-4">
            <span className="text-2xl font-bold text-white">K{price?.toFixed(2) || '---'}</span>
        </div>

        <div className="h-16 mt-2 -mx-2 opacity-80 group-hover:opacity-100 transition-opacity">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history && history.length > 0 ? history : []}>
                    <Line type="monotone" dataKey="value" stroke={change >= 0 ? "#10b981" : "#f43f5e"} strokeWidth={2} dot={false} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    </div>
);

interface Security {
    ticker: string;
    name: string;
    sector: string;
    price?: number;
    change?: number;
    history?: any[];
}

import { StockDetailModal } from './StockDetailModal';

export const MarketPulse = () => {
    const [securities, setSecurities] = useState<Security[]>([]);
    const [selectedStock, setSelectedStock] = useState<Security | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [downloading, setDownloading] = useState(false);

    const handleDownloadReport = async () => {
        try {
            setDownloading(true);
            const token = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!).access_token : null;
            const response = await fetch('http://localhost:8000/api/v1/reports/market-summary', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `LuSE_Market_Report_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error(err);
        } finally {
            setDownloading(false);
        }
    };

    useEffect(() => {
        const loadMarketData = async () => {
            try {
                // Fetch market summary directly
                const today = new Date().toISOString().split('T')[0];
                const response = await fetch(`http://localhost:8000/api/v1/market-data/market-summary?date=${today}`);
                if (!response.ok) {
                    throw new Error("Failed to fetch market summary");
                }
                const data = await response.json();

                const mapped = data.map((item: any) => ({
                    ...item,
                    change: item.change_percent
                }));

                setSecurities(mapped);
            } catch (err) {
                console.error("Failed to fetch securities", err);
                setError('Failed to fetch market data');
            } finally {
                setLoading(false);
            }
        };

        loadMarketData();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-brand-dark flex items-center justify-center text-white">
                <Loader2 className="w-10 h-10 animate-spin text-brand-primary" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-brand-dark flex items-center justify-center text-white">
                <p className="text-red-400">{error}</p>
            </div>
        )
    }

    return (
        <div className="p-6 space-y-8 animate-in fade-in duration-700 bg-brand-dark min-h-screen text-slate-100 font-sans">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-brand-primary to-emerald-400 bg-clip-text text-transparent">LuSE Market Pulse</h1>
                    <p className="text-brand-secondary mt-1">Real-time Bitemporal Data Stream</p>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={handleDownloadReport}
                        disabled={downloading}
                        className="flex items-center gap-2 px-3 py-2 bg-brand-primary/10 hover:bg-brand-primary/20 text-brand-primary rounded-lg text-sm transition-colors border border-brand-primary/20"
                    >
                        {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                        Export PDF
                    </button>
                    <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-lg border border-white/10">
                        <Activity className="w-4 h-4 text-brand-primary" />
                        <span className="text-sm font-mono">LASI: 6,420.21 (+0.4%)</span>
                    </div>
                </div>
            </header>

            <section>
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-emerald-400" /> Market Snapshot
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {securities.length === 0 ? (
                        <div className="col-span-4 text-center text-brand-secondary">No market data available. Ensure backend is running and seeded.</div>
                    ) : (
                        securities.map(s => (
                            <TickerCard
                                key={s.ticker}
                                {...s as any}
                                onClick={() => setSelectedStock(s)}
                            />
                        ))
                    )}
                </div>
            </section>

            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                    <h3 className="text-lg font-semibold mb-6">LuSE All Share Index (LASI) Performance</h3>
                    <div className="h-64 flex items-center justify-center text-brand-secondary">
                        {/* Placeholder for Main Index Chart */}
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={mockData.map(d => ({ ...d, value: d.value * 1500 }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                                <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={3} activeDot={{ r: 8 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                    <h3 className="text-lg font-semibold mb-4">Market Depth</h3>
                    <div className="space-y-4">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="flex justify-between text-sm py-2 border-b border-white/5 last:border-0 hover:bg-white/5 px-2 rounded cursor-pointer">
                                <span className="text-brand-secondary">10:4{i} AM</span>
                                <span className="font-mono text-emerald-400">BUY 500 ZANACO @ K4.35</span>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <StockDetailModal
                isOpen={!!selectedStock}
                onClose={() => setSelectedStock(null)}
                stock={selectedStock as any}
            />
        </div>
    );
};
