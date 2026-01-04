import { useState, useEffect, useRef, useMemo } from 'react';
import { Activity, DollarSign, Loader2, Download, FileSpreadsheet, ChevronDown, TrendingUp, TrendingDown, Info, BarChart3 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { cn } from '../lib/utils';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';




const TickerCard = ({ ticker, name, price, change, sector, history, onClick }: { ticker: string, name: string, price: number, change: number, sector: string, history: any[], onClick: () => void }) => (
    <div
        onClick={onClick}
        className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-md border border-white/20 rounded-xl p-5 shadow-xl hover:scale-[1.03] hover:border-brand-primary/50 hover:shadow-brand-primary/20 transition-all duration-300 cursor-pointer group relative overflow-hidden"
    >
        {/* Glow effect on hover */}
        <div className="absolute inset-0 bg-gradient-to-r from-brand-primary/0 via-brand-primary/5 to-brand-primary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="relative z-10">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="text-xl font-bold text-white group-hover:text-brand-primary transition-colors">{ticker}</h3>
                    <p className="text-xs text-slate-400 truncate w-32" title={name}>{name}</p>
                    <div className="mt-1.5">
                        <span className="text-[10px] uppercase tracking-wider bg-white/5 px-2 py-0.5 rounded text-slate-400">{sector}</span>
                    </div>
                </div>
                <div className="text-right">
                    <span className={cn("px-2.5 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1",
                        change >= 0 ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    )}>
                        {change >= 0 ? '↑' : '↓'} {change > 0 ? "+" : ""}{change.toFixed(2)}%
                    </span>
                </div>
            </div>

            {/* Price - Main Focus */}
            <div className="bg-black/20 rounded-lg px-3 py-2 mb-3">
                <div className="text-xs text-slate-500 mb-0.5">Current Price</div>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-white tracking-tight">
                        {price != null ? `K${price.toFixed(2)}` : '---'}
                    </span>
                    <span className="text-xs text-slate-500">ZMW</span>
                </div>
            </div>

            {/* Sparkline Chart */}
            <div className="h-14 -mx-1 opacity-80 group-hover:opacity-100 transition-opacity">
                {history && history.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={history}>
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke={change >= 0 ? "#10b981" : "#f43f5e"}
                                strokeWidth={2}
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-full flex items-center justify-center text-xs text-slate-500">No chart data</div>
                )}
            </div>

            {/* Click hint */}
            <div className="mt-2 text-[10px] text-slate-500 text-center opacity-0 group-hover:opacity-100 transition-opacity">
                Click for details & forecast →
            </div>
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
    const [downloadingSpreadsheet, setDownloadingSpreadsheet] = useState(false);
    const [exportMenuOpen, setExportMenuOpen] = useState(false);
    const exportMenuRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
                setExportMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleDownloadSpreadsheet = () => {
        try {
            setDownloadingSpreadsheet(true);

            // Create CSV content with Summary Section
            const dateStr = new Date().toISOString().split('T')[0];
            const summaryRows = [
                ['LuSE Market Pulse Report'],
                [`Generated: ${dateStr}`],
                [''],
                ['MARKET SUMMARY'],
                ['Market Status', marketStats ? (marketStats.advanceDeclineRatio >= 1 ? 'Bullish' : 'Bearish') : 'N/A'],
                ['Gainers', marketStats?.gainersCount ?? 0],
                ['Losers', marketStats?.losersCount ?? 0],
                ['Unchanged', marketStats?.unchangedCount ?? 0],
                ['Advance/Decline Ratio', marketStats?.advanceDeclineRatio.toFixed(2) ?? '0.00'],
                [''],
                ['SECURITIES DATA']
            ];

            const headers = ['Ticker', 'Name', 'Sector', 'Price (ZMW)', 'Change', 'Change %'];
            const dataRows = securities.map(s => [
                s.ticker,
                s.name,
                s.sector,
                s.price?.toFixed(2) ?? 'N/A',
                (s.change ?? 0).toFixed(2),
                `${((s as any).change_percent ?? 0).toFixed(2)}%`
            ]);

            const csvContent = [
                ...summaryRows.map(row => row.map(cell => `"${cell}"`).join(',')),
                headers.join(','),
                ...dataRows.map(row => row.map(cell => `"${cell}"`).join(','))
            ].join('\n');

            // Create and download the file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `LuSE_Market_Data_${dateStr}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Spreadsheet export failed:', err);
            setError('Failed to export CSV');
            setTimeout(() => setError(''), 3000);
        } finally {
            setDownloadingSpreadsheet(false);
        }
    };

    const handleDownloadPDF = async () => {
        try {
            setDownloading(true);
            const element = document.getElementById('market-pulse-container');
            if (!element) throw new Error('Element not found');

            // Capture the element
            const canvas = await html2canvas(element, {
                scale: 2, // High resolution
                useCORS: true,
                logging: false,
                backgroundColor: '#0f172a' // Ensure background color matches brand-dark
            });

            // Generate PDF
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF({
                orientation: 'landscape',
                unit: 'px',
                format: [canvas.width / 2, canvas.height / 2] // Scale down to fit standard view size but keep ratio
            });

            pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2);
            pdf.save(`LuSE_Market_Pulse_${new Date().toISOString().split('T')[0]}.pdf`);

        } catch (err) {
            console.error('PDF export failed:', err);
            setError('Failed to generate PDF report');
            setTimeout(() => setError(''), 3000);
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

                const mapped = data.map((item: any) => {
                    // Get price from the latest history entry if price is null
                    let displayPrice = item.price;
                    if (displayPrice == null && item.history && item.history.length > 0) {
                        // Sort by date descending and get latest
                        const sortedHistory = [...item.history].sort((a: any, b: any) =>
                            new Date(b.date).getTime() - new Date(a.date).getTime()
                        );
                        displayPrice = sortedHistory[0].value;
                    }

                    return {
                        ...item,
                        price: displayPrice,
                        change: item.change_percent ?? item.change ?? 0
                    };
                });

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

    // Calculated market statistics
    const marketStats = useMemo(() => {
        if (securities.length === 0) return null;

        const gainers = securities.filter(s => (s.change ?? 0) > 0);
        const losers = securities.filter(s => (s.change ?? 0) < 0);
        const unchanged = securities.filter(s => (s.change ?? 0) === 0);

        const sortedByChange = [...securities].sort((a, b) => (b.change ?? 0) - (a.change ?? 0));
        const topGainers = sortedByChange.slice(0, 3).filter(s => (s.change ?? 0) > 0);
        const topLosers = sortedByChange.slice(-3).filter(s => (s.change ?? 0) < 0).reverse();

        // Calculate sector performance
        const sectorPerf: Record<string, { total: number; count: number }> = {};
        securities.forEach(s => {
            if (!sectorPerf[s.sector]) {
                sectorPerf[s.sector] = { total: 0, count: 0 };
            }
            sectorPerf[s.sector].total += (s.change ?? 0);
            sectorPerf[s.sector].count += 1;
        });

        const sectorData = Object.entries(sectorPerf).map(([sector, data]) => ({
            sector,
            avgChange: data.total / data.count,
        })).sort((a, b) => b.avgChange - a.avgChange);

        return {
            totalSecurities: securities.length,
            gainersCount: gainers.length,
            losersCount: losers.length,
            unchangedCount: unchanged.length,
            topGainers,
            topLosers,
            sectorData,
            advanceDeclineRatio: losers.length > 0 ? gainers.length / losers.length : gainers.length,
        };
    }, [securities]);

    // Market breadth data for visualization
    const breadthData = useMemo(() => {
        if (!marketStats) return [];
        return [
            { name: 'Gainers', value: marketStats.gainersCount, fill: '#10b981' },
            { name: 'Losers', value: marketStats.losersCount, fill: '#f43f5e' },
            { name: 'Unchanged', value: marketStats.unchangedCount, fill: '#64748b' },
        ];
    }, [marketStats]);

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
        <div id="market-pulse-container" className="p-6 space-y-8 animate-in fade-in duration-700 bg-brand-dark min-h-screen text-slate-100 font-sans">
            <header className="flex justify-between items-center mb-0">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-brand-primary to-emerald-400 bg-clip-text text-transparent">LuSE Market Pulse</h1>
                    <p className="text-brand-secondary mt-1">Real-time Bitemporal Data Stream</p>
                </div>
                <div className="flex gap-4">
                    {/* Export Dropdown */}
                    <div className="relative" ref={exportMenuRef}>
                        <button
                            onClick={() => setExportMenuOpen(!exportMenuOpen)}
                            className="flex items-center gap-2 px-3 py-2 bg-brand-primary/10 hover:bg-brand-primary/20 text-brand-primary rounded-lg text-sm transition-colors border border-brand-primary/20"
                        >
                            <Download className="w-4 h-4" />
                            Export
                            <ChevronDown className={cn("w-4 h-4 transition-transform", exportMenuOpen && "rotate-180")} />
                        </button>

                        {exportMenuOpen && (
                            <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-50 overflow-hidden">
                                <button
                                    onClick={() => {
                                        handleDownloadPDF();
                                        setExportMenuOpen(false);
                                    }}
                                    disabled={downloading}
                                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-200 hover:bg-white/10 transition-colors disabled:opacity-50"
                                >
                                    {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4 text-brand-primary" />}
                                    <span>Export as PDF</span>
                                </button>
                                <button
                                    onClick={() => {
                                        handleDownloadSpreadsheet();
                                        setExportMenuOpen(false);
                                    }}
                                    disabled={downloadingSpreadsheet}
                                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-200 hover:bg-white/10 transition-colors disabled:opacity-50 border-t border-white/5"
                                >
                                    {downloadingSpreadsheet ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4 text-emerald-400" />}
                                    <span>Export as CSV</span>
                                </button>
                            </div>
                        )}
                    </div>
                    <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-lg border border-white/10">
                        <Activity className="w-4 h-4 text-brand-primary" />
                        <span className="text-sm font-mono">LASI: 25,919.83 (+0.86%)</span>
                    </div>
                </div>
            </header>

            {/* Market Summary Section (Breadth & Movers) - Moved to Top */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Market Breadth & Sector Performance */}
                <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <BarChart3 className="w-5 h-5 text-blue-400" />
                            Market Breadth & Sector Performance
                        </h3>
                        <div className="flex items-center gap-2">
                            <Info className="w-4 h-4 text-slate-400" />
                            <span className="text-xs text-slate-400">Shows market health at a glance</span>
                        </div>
                    </div>

                    {marketStats && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Market Breadth Summary */}
                            <div className="space-y-4">
                                <div className="grid grid-cols-3 gap-3">
                                    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-center">
                                        <div className="text-2xl font-bold text-emerald-400">{marketStats.gainersCount}</div>
                                        <div className="text-xs text-emerald-300">Gainers</div>
                                    </div>
                                    <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-center">
                                        <div className="text-2xl font-bold text-rose-400">{marketStats.losersCount}</div>
                                        <div className="text-xs text-rose-300">Losers</div>
                                    </div>
                                    <div className="bg-slate-500/10 border border-slate-500/30 rounded-lg p-3 text-center">
                                        <div className="text-2xl font-bold text-slate-400">{marketStats.unchangedCount}</div>
                                        <div className="text-xs text-slate-300">Unchanged</div>
                                    </div>
                                </div>

                                {/* Advance/Decline Indicator */}
                                <div className="bg-white/5 rounded-lg p-4">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm text-slate-400">Advance/Decline Ratio</span>
                                        <span className={cn(
                                            "text-lg font-bold",
                                            marketStats.advanceDeclineRatio >= 1 ? "text-emerald-400" : "text-rose-400"
                                        )}>
                                            {marketStats.advanceDeclineRatio.toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full"
                                            style={{ width: `${(marketStats.gainersCount / marketStats.totalSecurities) * 100}%` }}
                                        />
                                    </div>
                                    <p className="text-xs text-slate-500 mt-2">
                                        {marketStats.advanceDeclineRatio >= 1
                                            ? "✓ Bullish: More stocks advancing than declining"
                                            : "⚠ Bearish: More stocks declining than advancing"}
                                    </p>
                                </div>
                            </div>

                            {/* Sector Performance Chart */}
                            <div>
                                <div className="text-sm text-slate-400 mb-2">Sector Performance (Avg. Change %)</div>
                                <div className="h-48">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={marketStats.sectorData} layout="vertical">
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={true} vertical={false} />
                                            <XAxis type="number" stroke="#94a3b8" tickFormatter={(v) => `${v.toFixed(1)}%`} />
                                            <YAxis dataKey="sector" type="category" stroke="#94a3b8" width={70} tick={{ fontSize: 11 }} />
                                            <Tooltip
                                                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Avg Change']}
                                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            />
                                            <Bar dataKey="avgChange" radius={[0, 4, 4, 0]}>
                                                {marketStats.sectorData.map((entry, index) => (
                                                    <Cell
                                                        key={`cell-${index}`}
                                                        fill={entry.avgChange >= 0 ? '#10b981' : '#f43f5e'}
                                                    />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Top Movers */}
                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-purple-400" />
                        Top Movers
                    </h3>

                    {marketStats && (
                        <div className="space-y-4">
                            {/* Top Gainers */}
                            <div>
                                <div className="text-xs text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                                    <TrendingUp className="w-3 h-3" /> Top Gainers
                                </div>
                                <div className="space-y-2">
                                    {marketStats.topGainers.length > 0 ? (
                                        marketStats.topGainers.map((s, i) => (
                                            <div
                                                key={s.ticker}
                                                onClick={() => setSelectedStock(s)}
                                                className="flex justify-between items-center py-2 px-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/10 cursor-pointer transition"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span className="text-emerald-400 font-bold text-sm">#{i + 1}</span>
                                                    <span className="font-medium text-white">{s.ticker}</span>
                                                </div>
                                                <span className="text-emerald-400 font-mono text-sm">+{(s.change ?? 0).toFixed(2)}%</span>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-sm text-slate-500 text-center py-2">No gainers today</div>
                                    )}
                                </div>
                            </div>

                            {/* Top Losers */}
                            <div>
                                <div className="text-xs text-rose-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                                    <TrendingDown className="w-3 h-3" /> Top Losers
                                </div>
                                <div className="space-y-2">
                                    {marketStats.topLosers.length > 0 ? (
                                        marketStats.topLosers.map((s, i) => (
                                            <div
                                                key={s.ticker}
                                                onClick={() => setSelectedStock(s)}
                                                className="flex justify-between items-center py-2 px-3 bg-rose-500/5 border border-rose-500/20 rounded-lg hover:bg-rose-500/10 cursor-pointer transition"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span className="text-rose-400 font-bold text-sm">#{i + 1}</span>
                                                    <span className="font-medium text-white">{s.ticker}</span>
                                                </div>
                                                <span className="text-rose-400 font-mono text-sm">{(s.change ?? 0).toFixed(2)}%</span>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-sm text-slate-500 text-center py-2">No losers today</div>
                                    )}
                                </div>
                            </div>

                            {/* Insight */}
                            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 mt-4">
                                <p className="text-xs text-blue-200">
                                    <strong>💡 Insight:</strong> Top movers help identify momentum - gainers may indicate positive news or sector strength,
                                    while losers may present value opportunities or signal caution.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            {/* Market Snapshot Section (Detailed List) - Moved to Bottom */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <DollarSign className="w-5 h-5 text-emerald-400" /> Market Snapshot
                    </h2>
                    <span className="text-sm text-slate-400 bg-white/5 px-3 py-0.5 rounded-full">
                        {securities.length} Securities Listed
                    </span>
                </div>

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

            <StockDetailModal
                isOpen={!!selectedStock}
                onClose={() => setSelectedStock(null)}
                stock={selectedStock as any}
            />
        </div>
    );
};
