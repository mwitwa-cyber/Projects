import { useState } from 'react';
import { analyticsService } from '../services/analytics';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { RefreshCw, Play } from 'lucide-react';

interface AssetWeight {
    ticker: string;
    weight: number;
}

export const BacktestStrategy = () => {
    const [assets, setAssets] = useState<AssetWeight[]>([{ ticker: 'ZNCO', weight: 1.0 }]);
    const [startDate, setStartDate] = useState('2023-01-01');
    const [capital, setCapital] = useState(10000);
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAddAsset = () => {
        setAssets([...assets, { ticker: '', weight: 0 }]);
    };

    const handleRemoveAsset = (index: number) => {
        setAssets(assets.filter((_, i) => i !== index));
    };

    const updateAsset = (index: number, field: keyof AssetWeight, value: string | number) => {
        const newAssets = [...assets];
        // @ts-ignore
        newAssets[index][field] = value;
        setAssets(newAssets);
    };

    const runBacktest = async () => {
        setLoading(true);
        setError(null);
        try {
            // Convert array to dict
            const weights: Record<string, number> = {};
            assets.forEach(a => {
                if (a.ticker) weights[a.ticker] = Number(a.weight);
            });

            const res = await analyticsService.runBacktest(weights, startDate, capital);
            setResult(res);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Backtest failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in p-6">
            <h1 className="text-2xl font-bold text-gray-900">Strategy Backtester</h1>
            <p className="text-gray-500">Simulate portfolio performance using historical data.</p>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Controls */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 space-y-4 h-fit">
                    <h2 className="text-lg font-semibold">Configuration</h2>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Initial Capital</label>
                        <input
                            type="number"
                            value={capital}
                            onChange={(e) => setCapital(Number(e.target.value))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Start Date</label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700">Portfolio Allocation</label>
                        {assets.map((asset, idx) => (
                            <div key={idx} className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Ticker (e.g. ZNCO)"
                                    value={asset.ticker}
                                    onChange={(e) => updateAsset(idx, 'ticker', e.target.value)}
                                    className="flex-1 rounded-md border-gray-300 shadow-sm p-2 border uppercase"
                                />
                                <input
                                    type="number"
                                    placeholder="Wgt (0-1)"
                                    value={asset.weight}
                                    onChange={(e) => updateAsset(idx, 'weight', e.target.value)}
                                    className="w-24 rounded-md border-gray-300 shadow-sm p-2 border"
                                />
                                {assets.length > 1 && (
                                    <button onClick={() => handleRemoveAsset(idx)} className="text-red-500 px-2">×</button>
                                )}
                            </div>
                        ))}
                        <button onClick={handleAddAsset} className="text-sm text-blue-600 hover:text-blue-800">
                            + Add Asset
                        </button>
                    </div>

                    <button
                        onClick={runBacktest}
                        disabled={loading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {loading ? <RefreshCw className="animate-spin w-4 h-4" /> : <Play className="w-4 h-4" />}
                        Run Backtest
                    </button>

                    {error && (
                        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md">
                            {error}
                        </div>
                    )}
                </div>

                {/* Results */}
                <div className="lg:col-span-2 space-y-6">
                    {result ? (
                        <>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <MetricCard label="Total Return" value={`${(result.metrics.total_return * 100).toFixed(2)}%`} color={result.metrics.total_return >= 0 ? "text-green-600" : "text-red-600"} />
                                <MetricCard label="CAGR" value={`${(result.metrics.cagr * 100).toFixed(2)}%`} />
                                <MetricCard label="Sharpe Ratio" value={result.metrics.sharpe_ratio} />
                                <MetricCard label="Max Drawdown" value={`${(result.metrics.max_drawdown * 100).toFixed(2)}%`} color="text-red-600" />
                            </div>

                            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 h-[400px]">
                                <h3 className="text-lg font-semibold mb-4">Equity Curve</h3>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={result.equity_curve}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis dataKey="time" tickFormatter={(t) => t.substring(0, 10)} minTickGap={30} />
                                        <YAxis domain={['auto', 'auto']} />
                                        <Tooltip
                                            labelFormatter={(l) => l.substring(0, 10)}
                                            formatter={(val: any) => [`${val?.toFixed(2)} ZMW`, 'Equity']}
                                        />
                                        <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
                            <Play className="w-12 h-12 mb-2 opacity-20" />
                            <p>Configure portfolio and run backtest to see results</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const MetricCard = ({ label, value, color = "text-gray-900" }: { label: string, value: string | number, color?: string }) => (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
        <div className="text-sm text-gray-500">{label}</div>
        <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
);
