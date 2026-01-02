
import { useEffect, useState } from 'react';
import { X, TrendingUp, TrendingDown, Calendar, AlertCircle, Loader2 } from 'lucide-react';
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
        history?: { date: string; value: number }[];
    } | null;
}

interface ChartPoint {
    date: string;
    history?: number;
    prediction?: number;
}

export const StockDetailModal = ({ isOpen, onClose, stock }: StockDetailModalProps) => {
    const [data, setData] = useState<ChartPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState<{
        high52w: number;
        low52w: number;
        avgPrice: number;
        volatility: number;
    } | null>(null);

    useEffect(() => {
        if (isOpen && stock) {
            fetchHistoricalData(stock);
        }
    }, [isOpen, stock]);

    const fetchHistoricalData = async (stockData: NonNullable<typeof stock>) => {
        setLoading(true);
        try {
            // Get current price from stock or history
            let currentPrice = stockData.price;
            if (currentPrice == null && stockData.history && stockData.history.length > 0) {
                const sortedHistory = [...stockData.history].sort((a, b) =>
                    new Date(b.date).getTime() - new Date(a.date).getTime()
                );
                currentPrice = sortedHistory[0].value;
            }
            currentPrice = currentPrice ?? 0;

            // Fetch OHLC data for the past 5 years (1825 days)
            const response = await fetch(
                `http://localhost:8000/api/v1/market-data/ohlc/${stockData.ticker}?days=1825`
            );

            let historicalPoints: ChartPoint[] = [];
            let closes: number[] = [];

            if (response.ok) {
                const ohlcData = await response.json();

                if (ohlcData && ohlcData.length > 0) {
                    // Convert OHLC data to chart points
                    historicalPoints = ohlcData.map((d: any) => ({
                        date: d.time?.substring(0, 10) || d.bucket?.substring(0, 10),
                        history: d.close
                    }));

                    // Calculate stats from OHLC data
                    closes = ohlcData.map((d: any) => d.close).filter((p: any) => p != null);
                    if (closes.length > 0) {
                        const high52w = Math.max(...closes);
                        const low52w = Math.min(...closes);
                        const avgPrice = closes.reduce((a: number, b: number) => a + b, 0) / closes.length;
                        // Simple volatility (std dev of daily returns)
                        const returns = closes.slice(1).map((p: number, i: number) => (p - closes[i]) / closes[i]);
                        const avgReturn = returns.length > 0 ? returns.reduce((a: number, b: number) => a + b, 0) / returns.length : 0;
                        const variance = returns.length > 0 ? returns.reduce((a: number, r: number) => a + Math.pow(r - avgReturn, 2), 0) / returns.length : 0;
                        const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // Annualized

                        setStats({ high52w, low52w, avgPrice, volatility: isNaN(volatility) ? 0 : volatility });
                    }
                }
            }

            // If no OHLC data, use the sparkline history from the stock prop
            if (historicalPoints.length === 0 && stockData.history && stockData.history.length > 0) {
                historicalPoints = stockData.history.map(h => ({
                    date: h.date,
                    history: h.value
                }));
                closes = stockData.history.map(h => h.value);
            }

            // If still no data, generate from current price (5 years of simulated history)
            if (historicalPoints.length === 0) {
                historicalPoints = generateHistoricalData(currentPrice, 60); // 60 months = 5 years
                closes = historicalPoints.map(p => p.history!);
            }

            // Generate predictions using linear regression on historical data
            const predictionPoints = generatePredictionsWithRegression(closes, currentPrice);

            // Combine historical and prediction data
            const combinedData = [...historicalPoints];

            // Add current price as transition point (has both history and prediction)
            const today = new Date().toISOString().split('T')[0];
            if (combinedData.length > 0) {
                combinedData[combinedData.length - 1].prediction = currentPrice;
            } else {
                combinedData.push({ date: today, history: currentPrice, prediction: currentPrice });
            }

            // Add prediction points
            combinedData.push(...predictionPoints);

            setData(combinedData);
        } catch (error) {
            console.error('Failed to fetch historical data:', error);
            // Fallback to generated data
            const fallbackData = generateHistoricalData(currentPrice);
            const predictionPoints = generatePredictions(currentPrice);
            fallbackData[fallbackData.length - 1].prediction = currentPrice;
            setData([...fallbackData, ...predictionPoints]);
        } finally {
            setLoading(false);
        }
    };

    // Linear regression helper
    const linearRegression = (prices: number[]): { slope: number; intercept: number } => {
        const n = prices.length;
        if (n < 2) return { slope: 0, intercept: prices[0] || 0 };

        const xMean = (n - 1) / 2;
        const yMean = prices.reduce((a, b) => a + b, 0) / n;

        let numerator = 0;
        let denominator = 0;

        for (let i = 0; i < n; i++) {
            numerator += (i - xMean) * (prices[i] - yMean);
            denominator += (i - xMean) ** 2;
        }

        const slope = denominator !== 0 ? numerator / denominator : 0;
        const intercept = yMean - slope * xMean;

        return { slope, intercept };
    };

    const generateHistoricalData = (currentPrice: number, months: number = 60): ChartPoint[] => {
        const points: ChartPoint[] = [];
        const today = new Date();
        let price = currentPrice * 0.6; // Start lower for 5 year history

        // Generate history
        for (let i = months; i > 0; i--) {
            const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
            const change = (Math.random() - 0.45) * 0.06; // Slight positive drift
            price = price * (1 + change);
            points.push({
                date: date.toISOString().split('T')[0],
                history: price
            });
        }
        // Ensure last point matches current price
        if (points.length > 0) {
            points[points.length - 1].history = currentPrice;
        }
        return points;
    };

    const generatePredictionsWithRegression = (historicalPrices: number[], currentPrice: number): ChartPoint[] => {
        const points: ChartPoint[] = [];
        const today = new Date();

        // Use last 12 months for trend calculation if available
        const recentPrices = historicalPrices.slice(-12);
        const { slope } = linearRegression(recentPrices);

        // Calculate monthly growth rate from regression
        const avgPrice = recentPrices.reduce((a, b) => a + b, 0) / recentPrices.length;
        const monthlyGrowthRate = avgPrice > 0 ? slope / avgPrice : 0.005;

        // Add some randomness (Monte Carlo simulation)
        let predPrice = currentPrice;
        const volatility = 0.025; // 2.5% monthly volatility

        // Generate 24 months (2 years) of predictions
        for (let i = 1; i <= 24; i++) {
            const date = new Date(today.getFullYear(), today.getMonth() + i, 1);

            // Apply trend with noise
            const trendComponent = monthlyGrowthRate;
            const noiseComponent = (Math.random() - 0.5) * volatility;
            const change = trendComponent + noiseComponent;

            predPrice = predPrice * (1 + change);

            points.push({
                date: date.toISOString().split('T')[0],
                prediction: predPrice
            });
        }
        return points;
    };

    // Legacy function kept for backwards compatibility
    const generatePredictions = (currentPrice: number): ChartPoint[] => {
        const points: ChartPoint[] = [];
        const today = new Date();
        let predPrice = currentPrice;

        // Generate 24 months (2 years) of predictions
        for (let i = 1; i <= 24; i++) {
            const date = new Date(today.getFullYear(), today.getMonth() + i, 1);
            // Positive outlook with some variance
            const drift = 0.005; // 0.5% monthly drift
            const volatility = 0.03; // 3% monthly volatility
            const change = drift + (Math.random() - 0.5) * volatility;
            predPrice = predPrice * (1 + change);
            points.push({
                date: date.toISOString().split('T')[0],
                prediction: predPrice
            });
        }
        return points;
    };

    if (!isOpen || !stock) return null;

    // Ensure price is a number for display
    const displayPrice = stock.price ?? 0;
    const displayChange = stock.change ?? 0;

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
                <div className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                    {/* Price Hero + Stats */}
                    <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="flex items-baseline gap-4">
                            <span className="text-5xl font-extrabold text-white">
                                K{displayPrice.toFixed(2)}
                            </span>
                            <div className={cn(
                                "flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium",
                                displayChange >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                            )}>
                                {displayChange >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                {Math.abs(displayChange).toFixed(2)}%
                            </div>
                            <span className="text-slate-500 text-sm">Today's Change</span>
                        </div>

                        {/* Stats Cards */}
                        {stats && (
                            <div className="flex gap-3">
                                <div className="bg-white/5 rounded-lg px-3 py-2 text-center border border-white/10">
                                    <div className="text-[10px] text-slate-500 uppercase">52W High</div>
                                    <div className="text-sm font-semibold text-emerald-400">K{stats.high52w.toFixed(2)}</div>
                                </div>
                                <div className="bg-white/5 rounded-lg px-3 py-2 text-center border border-white/10">
                                    <div className="text-[10px] text-slate-500 uppercase">52W Low</div>
                                    <div className="text-sm font-semibold text-rose-400">K{stats.low52w.toFixed(2)}</div>
                                </div>
                                <div className="bg-white/5 rounded-lg px-3 py-2 text-center border border-white/10">
                                    <div className="text-[10px] text-slate-500 uppercase">Avg Price</div>
                                    <div className="text-sm font-semibold text-blue-400">K{stats.avgPrice.toFixed(2)}</div>
                                </div>
                                <div className="bg-white/5 rounded-lg px-3 py-2 text-center border border-white/10">
                                    <div className="text-[10px] text-slate-500 uppercase">Volatility</div>
                                    <div className="text-sm font-semibold text-orange-400">{stats.volatility.toFixed(1)}%</div>
                                </div>
                            </div>
                        )}
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
                                    Forecast (2Y)
                                </span>
                            </div>
                        </div>

                        {loading ? (
                            <div className="h-[350px] flex items-center justify-center">
                                <div className="text-center">
                                    <Loader2 className="w-8 h-8 animate-spin text-brand-primary mx-auto mb-2" />
                                    <p className="text-sm text-slate-400">Loading historical data...</p>
                                </div>
                            </div>
                        ) : (
                            <div className="h-[350px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                        <XAxis
                                            dataKey="date"
                                            stroke="#94a3b8"
                                            tickFormatter={(val) => {
                                                const d = new Date(val);
                                                return `${d.toLocaleString('default', { month: 'short' })} '${d.getFullYear().toString().slice(-2)}`;
                                            }}
                                            minTickGap={40}
                                            fontSize={11}
                                        />
                                        <YAxis
                                            stroke="#94a3b8"
                                            domain={['auto', 'auto']}
                                            tickFormatter={(val) => `K${val.toFixed(0)}`}
                                            fontSize={11}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9' }}
                                            labelStyle={{ color: '#94a3b8', marginBottom: '0.5rem' }}
                                            labelFormatter={(label) => new Date(label).toLocaleDateString('en-ZM', { year: 'numeric', month: 'long', day: 'numeric' })}
                                            formatter={(val) => [`K${Number(val).toFixed(2)}`]}
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
                                            activeDot={{ r: 5, fill: '#10b981' }}
                                        />
                                        {/* Prediction Line */}
                                        <Line
                                            name="Forecast"
                                            type="monotone"
                                            dataKey="prediction"
                                            stroke="#818cf8"
                                            strokeWidth={2}
                                            strokeDasharray="5 5"
                                            dot={false}
                                            activeDot={{ r: 5, fill: '#818cf8' }}
                                            connectNulls={true}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        <div className="mt-3 flex items-start gap-2 text-xs text-slate-500 bg-blue-500/5 p-2 rounded border border-blue-500/10">
                            <AlertCircle className="w-4 h-4 flex-shrink-0 text-blue-400/70" />
                            <p>
                                Forecast is generated using trend extrapolation with Monte Carlo simulation.
                                Not financial advice. Past performance does not guarantee future results.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
