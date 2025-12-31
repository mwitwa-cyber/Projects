import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { Loader2, AlertCircle, PieChart as PieChartIcon, Trash2 } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, ScatterChart, Scatter, CartesianGrid, XAxis, YAxis } from 'recharts';
import { optimizationAPI } from '../services/api';

// Asset type definition
interface Asset {
    ticker: string;
    returns: number[];
}

// Optimization API result type
interface OptimizationResult {
    optimal_weights: Record<string, number>;
    expected_return: number;
    portfolio_volatility: number;
    sharpe_ratio: number;
}

// Efficient frontier API result type
interface FrontierResult {
    frontierPoints: Array<{ volatility: number; return: number }>;
    optimalPoint: { volatility: number; return: number };
}

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

/**
 * PortfolioOptimizer component: UI for multi-asset portfolio optimization and visualization.
 */
export const PortfolioOptimizer = () => {
    const [assets, setAssets] = useState<Asset[]>([
        { ticker: 'CECZ', returns: [0.02, 0.03, -0.01, 0.04, 0.01, 0.02, -0.02, 0.03] },
        { ticker: 'ZANACO', returns: [0.01, 0.02, 0.01, 0.02, 0.03, 0.01, 0.02, 0.01] },
        { ticker: 'SCBL', returns: [0.015, 0.025, 0.005, 0.03, 0.02, 0.01, 0.03, 0.025] },
    ]);
    const [riskFreeRate, setRiskFreeRate] = useState<number>(0.20);
    const [objective, setObjective] = useState<'max_sharpe' | 'min_variance' | 'equal_weight'>('max_sharpe');
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [frontierData, setFrontierData] = useState<FrontierResult | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
    const [activeTab, setActiveTab] = useState<'weights' | 'frontier'>('weights');

    const [availableSecurities, setAvailableSecurities] = useState<string[]>([]);

    useEffect(() => {
        const fetchSecurities = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/v1/market-data/securities');
                if (response.ok) {
                    const data = await response.json();
                    setAvailableSecurities(data.map((s: any) => s.ticker));
                }
            } catch (err) {
                console.error("Failed to fetch securities", err);
            }
        };
        fetchSecurities();
    }, []);

    // Add a new asset row
    const addAsset = () => {
        setAssets([...assets, { ticker: availableSecurities[0] || '', returns: [] }]);
    };

    // Remove an asset row by index
    const removeAsset = (index: number) => {
        setAssets(assets.filter((_, i) => i !== index));
    };

    // Update asset ticker or returns
    const updateAsset = (index: number, field: 'ticker' | 'returns', value: string) => {
        const newAssets = [...assets];
        if (field === 'returns') {
            newAssets[index].returns = value.split(',').map((v: string) => parseFloat(v.trim())).filter((v) => !isNaN(v));
        } else {
            newAssets[index].ticker = value.toUpperCase();
        }
        setAssets(newAssets);
    };

    // Handle optimization form submit
    const handleOptimize = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setResult(null);

        try {
            const returnsData: Record<string, number[]> = {};
            assets.forEach(asset => {
                if (asset.ticker && asset.returns.length > 0) {
                    returnsData[asset.ticker] = asset.returns;
                }
            });

            if (Object.keys(returnsData).length === 0) {
                setError('Please add at least one asset with returns data');
                setLoading(false);
                return;
            }

            const data = await optimizationAPI.optimize({
                returns_data: returnsData,
                objective,
                risk_free_rate: riskFreeRate,
            });

            setResult(data);

            // Also fetch efficient frontier
            const frontierResult = await optimizationAPI.efficientFrontier({
                returns_data: returnsData,
                num_points: 50,
                risk_free_rate: riskFreeRate,
            });

            setFrontierData(frontierResult);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Optimization failed');
        } finally {
            setLoading(false);
        }
    };

    const getWeightPieData = () => {
        if (!result) return [];
        return Object.entries(result.optimal_weights)
            .filter(([_, weight]) => weight > 0.001)
            .map(([ticker, weight]) => ({
                name: ticker,
                value: Math.round(weight * 100),
            }));
    };

    const getFrontierChartData = () => {
        if (!frontierData) return [];
        return frontierData.frontierPoints.map(point => ({
            volatility: Number((point.volatility * 100).toFixed(2)),
            return: Number((point.return * 100).toFixed(2)),
        }));
    };

    return (
        <div className="space-y-6">
            {/* Input Section */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
                <h2 className="text-2xl font-bold text-white mb-6">Portfolio Optimizer</h2>

                <form onSubmit={handleOptimize} className="space-y-6">
                    {/* Objectives */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-3">
                            Optimization Objective
                        </label>
                        <div className="flex gap-4">
                            {(['max_sharpe', 'min_variance', 'equal_weight'] as const).map(opt => (
                                <label key={opt} className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="objective"
                                        value={opt}
                                        checked={objective === opt}
                                        onChange={(e) => setObjective(e.target.value as any)}
                                        className="w-4 h-4"
                                    />
                                    <span className="text-sm text-slate-300">
                                        {opt === 'max_sharpe' && 'Maximize Sharpe Ratio'}
                                        {opt === 'min_variance' && 'Minimize Variance'}
                                        {opt === 'equal_weight' && 'Equal Weight'}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Risk-Free Rate */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Risk-Free Rate (% p.a.)
                        </label>
                        <input
                            type="number"
                            value={riskFreeRate * 100}
                            onChange={(e) => setRiskFreeRate(parseFloat(e.target.value) / 100)}
                            step="0.1"
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-400"
                        />
                    </div>

                    {/* Assets */}
                    <div>
                        <div className="flex justify-between items-center mb-3">
                            <label className="block text-sm font-medium text-slate-300">
                                Assets (Enter returns as comma-separated values)
                            </label>
                            <button
                                type="button"
                                onClick={addAsset}
                                className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                            >
                                + Add Asset
                            </button>
                        </div>

                        <div className="space-y-3 max-h-48 overflow-y-auto">
                            {assets.map((asset, idx) => (
                                <div key={idx} className="flex gap-3">
                                    <select
                                        value={asset.ticker}
                                        onChange={(e) => updateAsset(idx, 'ticker', e.target.value)}
                                        className="w-32 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400 [&>option]:bg-slate-800 [&>option]:text-white"
                                    >
                                        <option value="" disabled>Select Asset</option>
                                        {availableSecurities.length > 0 ? (
                                            availableSecurities.map(t => (
                                                <option key={t} value={t}>{t}</option>
                                            ))
                                        ) : (
                                            // Fallback if fetch fails or loading
                                            <option value={asset.ticker}>{asset.ticker || 'Loading...'}</option>
                                        )}
                                    </select>
                                    <input
                                        type="text"
                                        value={asset.returns.join(', ')}
                                        onChange={(e) => updateAsset(idx, 'returns', e.target.value)}
                                        placeholder="0.02, 0.03, -0.01, 0.04"
                                        className="flex-1 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-slate-400 text-sm focus:outline-none focus:border-blue-400"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => removeAsset(idx)}
                                        className="text-red-400 hover:text-red-300 p-2"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold py-3 rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Optimizing...
                            </>
                        ) : (
                            'Optimize Portfolio'
                        )}
                    </button>
                </form>

                {error && (
                    <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                        <div className="text-red-200 text-sm">{error}</div>
                    </div>
                )}
            </div>

            {/* Results Section */}
            {result && (
                <div className="space-y-6">
                    {/* Performance Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Expected Return</div>
                            <div className="text-2xl font-bold text-green-400">
                                {(result.expected_return * 100).toFixed(2)}%
                            </div>
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Portfolio Volatility</div>
                            <div className="text-2xl font-bold text-orange-400">
                                {(result.portfolio_volatility * 100).toFixed(2)}%
                            </div>
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Sharpe Ratio</div>
                            <div className="text-2xl font-bold text-blue-400">
                                {result.sharpe_ratio.toFixed(3)}
                            </div>
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Risk-Free Rate</div>
                            <div className="text-2xl font-bold text-purple-400">
                                {(riskFreeRate * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-4 border-b border-white/10">
                        <button
                            onClick={() => setActiveTab('weights')}
                            className={`px-4 py-2 font-medium border-b-2 transition ${activeTab === 'weights'
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            Asset Allocation
                        </button>
                        <button
                            onClick={() => setActiveTab('frontier')}
                            className={`px-4 py-2 font-medium border-b-2 transition ${activeTab === 'frontier'
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            Efficient Frontier
                        </button>
                    </div>

                    {/* Weights Chart */}
                    {activeTab === 'weights' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                            <div className="flex items-center gap-2 mb-6">
                                <PieChartIcon className="w-5 h-5 text-blue-400" />
                                <h3 className="text-lg font-semibold text-white">Optimal Asset Allocation</h3>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={getWeightPieData()}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, value }) => `${name}: ${value}%`}
                                                outerRadius={80}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {getWeightPieData().map((_, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip formatter={(value: any) => `${value}%`} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="space-y-3">
                                    {Object.entries(result.optimal_weights)
                                        .filter(([_, weight]) => weight > 0.001)
                                        .map(([ticker, weight]) => (
                                            <div key={ticker} className="bg-white/5 rounded-lg p-3 flex justify-between items-center">
                                                <span className="font-semibold text-white">{ticker}</span>
                                                <div className="text-right">
                                                    <div className="text-lg font-bold text-emerald-400">
                                                        {(weight * 100).toFixed(1)}%
                                                    </div>
                                                    <div className="w-32 bg-white/10 rounded-full h-2 mt-1 overflow-hidden">
                                                        <div
                                                            className="bg-gradient-to-r from-emerald-500 to-green-400 h-full"
                                                            style={{ width: `${weight * 100}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Efficient Frontier */}
                    {activeTab === 'frontier' && frontierData && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                            <h3 className="text-lg font-semibold text-white mb-6">Efficient Frontier</h3>
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="volatility" name="Volatility (%)" stroke="#94a3b8" />
                                        <YAxis dataKey="return" name="Return (%)" stroke="#94a3b8" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: any) => value.toFixed(2)}
                                        />
                                        <Scatter
                                            name="Frontier"
                                            data={getFrontierChartData()}
                                            fill="#10b981"
                                            line
                                        />
                                        {frontierData.optimalPoint && (
                                            <Scatter
                                                name="Optimal Portfolio"
                                                data={[{
                                                    volatility: Number((frontierData.optimalPoint.volatility * 100).toFixed(2)),
                                                    return: Number((frontierData.optimalPoint.return * 100).toFixed(2)),
                                                }]}
                                                fill="#fbbf24"
                                                shape="star"
                                            />
                                        )}
                                    </ScatterChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
