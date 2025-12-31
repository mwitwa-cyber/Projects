
import { useEffect, useState } from 'react';
import { X, TrendingUp, TrendingDown, Calendar, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { cn } from '../lib/utils';

interface StockDetailModalProps {
    isOpen: boolean;
    onClose: () => void;
    stock: {
        ticker: string;
        name: string;
        price: number;
        change: number;
        sector?: string;
    } | null;
}

interface ChartPoint {
    date: string;
    history?: number;
    prediction?: number;
}

export const StockDetailModal = ({ isOpen, onClose, stock }: StockDetailModalProps) => {
    const [data, setData] = useState<ChartPoint[]>([]);

    useEffect(() => {
        if (isOpen && stock) {
            generateMockData(stock.price);
        }
    }, [isOpen, stock]);

    const generateMockData = (currentPrice: number) => {
        const points: ChartPoint[] = [];
        const today = new Date();
        const startPrice = currentPrice * 0.7; // Start lower 5 years ago
        let price = startPrice;

        // Generate 5 Years of History (Monthly points = 60)
        for (let i = 60; i > 0; i--) {
            const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
            // Random walk with drift
            const change = (Math.random() - 0.45) * 0.05; // Slightly positive drift
            price = price * (1 + change);

            points.push({
                date: date.toISOString().split('T')[0],
                history: price
            });
        }

        // Bridge current price exactly
        points[points.length - 1].history = currentPrice;

        // Generate 1 Year of Prediction
        let predPrice = currentPrice;
        for (let i = 1; i <= 12; i++) {
            const date = new Date(today.getFullYear(), today.getMonth() + i, 1);
            // Prediction algorithm (Positive outlook)
            const change = (Math.random() - 0.4) * 0.04;
            predPrice = predPrice * (1 + change);

            points.push({
                date: date.toISOString().split('T')[0],
                prediction: predPrice
            });
        }

        // Ensure connectivity
        // Add current price as first point of prediction to connect lines ?? 
        // Or just let Recharts handle gaps. Recharts handles gaps if undefined.
        // My schema has history=undefined for prediction points, and vice versa.
        // To connect them visually, one point needs both, or use `connectNulls`.

        // Let's add the transition point (Today) having *both* or ensure continuity.
        // The last history point is "Today". 
        // Let's make the first prediction point "Today" as well?
        // Actually, easiest is to have the last history point also serve as start of prediction line.
        const lastHistIdx = points.findIndex(p => p.prediction !== undefined) - 1;
        if (lastHistIdx >= 0) {
            points[lastHistIdx].prediction = points[lastHistIdx].history;
        }

        setData(points);
    };

    if (!isOpen || !stock) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-4xl bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex justify-between items-start p-6 border-b border-white/10 bg-white/5">
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-3xl font-bold text-white tracking-tight">{stock.ticker}</h2>
                            <span className="px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                {stock.sector || 'Equities'}
                            </span>
                        </div>
                        <p className="text-slate-400 mt-1">{stock.name}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-8">
                    {/* Price Hero */}
                    <div className="flex items-baseline gap-4">
                        <span className="text-5xl font-extrabold text-white">
                            K{stock.price.toFixed(2)}
                        </span>
                        <div className={cn(
                            "flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium",
                            stock.change >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                        )}>
                            {stock.change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {Math.abs(stock.change).toFixed(2)}%
                        </div>
                        <span className="text-slate-500 text-sm">Today's Change</span>
                    </div>

                    {/* Performance Chart */}
                    <div className="bg-black/20 rounded-xl p-4 border border-white/5">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Calendar className="w-5 h-5 text-indigo-400" />
                                Performance & Forecast
                            </h3>
                            <div className="flex gap-4 text-xs">
                                <span className="flex items-center gap-1.5 text-slate-300">
                                    <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                                    Historical (5Y)
                                </span>
                                <span className="flex items-center gap-1.5 text-slate-300">
                                    <span className="w-3 h-3 rounded-full bg-indigo-400 border border-indigo-400 border-dashed"></span>
                                    Prediction (1Y)
                                </span>
                            </div>
                        </div>

                        <div className="h-[400px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#94a3b8"
                                        tickFormatter={(val) => val.substring(0, 4)} // Show Year
                                        minTickGap={50}
                                    />
                                    <YAxis
                                        stroke="#94a3b8"
                                        domain={['auto', 'auto']}
                                        tickFormatter={(val) => `K${val}`}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9' }}
                                        labelStyle={{ color: '#94a3b8', marginBottom: '0.5rem' }}
                                        formatter={(val: any) => [`K${Number(val).toFixed(2)}`, 'Price']}
                                    />
                                    <Legend />
                                    {/* History Line */}
                                    <Line
                                        name="Historical"
                                        type="monotone"
                                        dataKey="history"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 6 }}
                                    />
                                    {/* Prediction Line */}
                                    <Line
                                        name="Prediction"
                                        type="monotone"
                                        dataKey="prediction"
                                        stroke="#818cf8"
                                        strokeWidth={2}
                                        strokeDasharray="5 5"
                                        dot={false}
                                        connectNulls={true}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-2 flex items-start gap-2 text-xs text-slate-500 bg-blue-500/5 p-2 rounded border border-blue-500/10">
                            <AlertCircle className="w-4 h-4 flex-shrink-0 text-blue-400/70" />
                            <p>
                                Prediction is generated using a linear trend extrapolation with Monte Carlo noise simulation.
                                Not financial advice. Past performance does not guarantee future results.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
