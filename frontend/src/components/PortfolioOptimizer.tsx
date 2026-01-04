import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import { Loader2, AlertCircle, PieChart as PieChartIcon, Trash2, Plus, TrendingUp, TrendingDown, RefreshCw, Info, CheckCircle } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, ScatterChart, Scatter, CartesianGrid, XAxis, YAxis, BarChart, Bar, Legend } from 'recharts';
import api, { optimizationAPI } from '../services/api';

// Type definitions
interface SecurityInfo {
    ticker: string;
    name: string;
    sector: string;
}

interface AssetReturnsData {
    ticker: string;
    returns: number[];
    periods: number;
    mean_return: number;
    volatility: number;
    start_date: string;
    end_date: string;
}

interface SelectedAsset {
    ticker: string;
    name: string;
    loaded: boolean;
    loading: boolean;
    error: string | null;
    data: AssetReturnsData | null;
}

interface OptimizationResult {
    weights: Record<string, number>;
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    objective: string;
}

interface FrontierResult {
    frontier: Array<{ volatility: number; return: number }>;
    n_points: number;
    assets: string[];
    optimalPoint?: { volatility: number; return: number };
}

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16', '#f472b6'];

/**
 * Enhanced PortfolioOptimizer with auto-fetch of historical returns
 */
export const PortfolioOptimizer = () => {
    // Available securities from backend
    const [availableSecurities, setAvailableSecurities] = useState<SecurityInfo[]>([]);
    const [loadingSecurities, setLoadingSecurities] = useState(true);

    // Selected assets for portfolio
    const [selectedAssets, setSelectedAssets] = useState<SelectedAsset[]>([]);

    // Optimization parameters
    const [riskFreeRate, setRiskFreeRate] = useState(0.13); // 13% Zambian T-bill
    const [objective, setObjective] = useState<'max_sharpe' | 'min_vol' | 'equal_weight'>('max_sharpe');
    const [lookbackPeriods, setLookbackPeriods] = useState(52); // 1 year weekly

    // Results
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [frontierData, setFrontierData] = useState<FrontierResult | null>(null);
    const [optimizing, setOptimizing] = useState(false);
    const [error, setError] = useState('');

    // UI state
    const [activeTab, setActiveTab] = useState<'weights' | 'frontier' | 'stats'>('weights');

    // Fetch available securities on mount
    useEffect(() => {
        const fetchSecurities = async () => {
            try {
                const response = await api.get('/market-data/securities');
                setAvailableSecurities(response.data);
            } catch (err) {
                console.error("Failed to fetch securities", err);
            } finally {
                setLoadingSecurities(false);
            }
        };
        fetchSecurities();
    }, []);

    // Fetch returns for a specific asset
    const fetchAssetReturns = useCallback(async (ticker: string) => {
        setSelectedAssets(prev => prev.map(a =>
            a.ticker === ticker ? { ...a, loading: true, error: null } : a
        ));

        try {
            const response = await api.get(`/market-data/returns/${ticker}`, {
                params: { periods: lookbackPeriods }
            });

            setSelectedAssets(prev => prev.map(a =>
                a.ticker === ticker ? {
                    ...a,
                    loading: false,
                    loaded: true,
                    data: response.data,
                    error: response.data.periods < 4 ? 'Insufficient data' : null
                } : a
            ));
        } catch (err) {
            setSelectedAssets(prev => prev.map(a =>
                a.ticker === ticker ? {
                    ...a,
                    loading: false,
                    loaded: false,
                    error: 'Failed to fetch returns'
                } : a
            ));
        }
    }, [lookbackPeriods]);

    // Add an asset to the portfolio
    const addAsset = (security: SecurityInfo) => {
        if (selectedAssets.some(a => a.ticker === security.ticker)) {
            return; // Already added
        }

        const newAsset: SelectedAsset = {
            ticker: security.ticker,
            name: security.name,
            loaded: false,
            loading: true,
            error: null,
            data: null
        };

        setSelectedAssets(prev => [...prev, newAsset]);
        fetchAssetReturns(security.ticker);
    };

    // Remove an asset
    const removeAsset = (ticker: string) => {
        setSelectedAssets(prev => prev.filter(a => a.ticker !== ticker));
        // Clear results if we modify the portfolio
        setResult(null);
        setFrontierData(null);
    };

    // Refresh all asset data
    const refreshAllData = () => {
        selectedAssets.forEach(asset => {
            fetchAssetReturns(asset.ticker);
        });
    };

    // Run optimization
    const handleOptimize = async (e: FormEvent) => {
        e.preventDefault();
        setOptimizing(true);
        setError('');
        setResult(null);

        try {
            // Build returns data from loaded assets
            const returnsData: Record<string, number[]> = {};
            let minLength = Infinity;

            selectedAssets.forEach(asset => {
                if (asset.data && asset.data.returns.length >= 4) {
                    returnsData[asset.ticker] = asset.data.returns;
                    minLength = Math.min(minLength, asset.data.returns.length);
                }
            });

            if (Object.keys(returnsData).length < 2) {
                setError('Please add at least 2 assets with sufficient historical data');
                setOptimizing(false);
                return;
            }

            // Align all returns to same length (use common period)
            Object.keys(returnsData).forEach(ticker => {
                returnsData[ticker] = returnsData[ticker].slice(-minLength);
            });

            // Run optimization
            const data = await optimizationAPI.optimize({
                returns_data: returnsData,
                objective,
                risk_free_rate: riskFreeRate,
            });

            setResult(data);

            // Also fetch efficient frontier
            const frontierResult = await optimizationAPI.efficientFrontier({
                returns_data: returnsData,
                n_points: 50,
                risk_free_rate: riskFreeRate,
            });

            setFrontierData(frontierResult);
        } catch (err: unknown) {
            const axiosError = err as { response?: { data?: { detail?: string } } };
            setError(axiosError.response?.data?.detail || 'Optimization failed');
        } finally {
            setOptimizing(false);
        }
    };

    // Helper: count ready assets
    const readyAssets = selectedAssets.filter(a => a.loaded && !a.error && a.data && a.data.periods >= 4);
    const canOptimize = readyAssets.length >= 2;

    // Chart data helpers
    const getWeightPieData = () => {
        if (!result) return [];
        return Object.entries(result.weights)
            .filter(([, weight]) => weight > 0.001)
            .map(([ticker, weight]) => ({
                name: ticker,
                value: Math.round(weight * 100),
            }));
    };

    const getFrontierChartData = () => {
        if (!frontierData) return [];
        return frontierData.frontier.map(point => ({
            volatility: Number((point.volatility * 100).toFixed(2)),
            return: Number((point.return * 100).toFixed(2)),
        }));
    };

    const getAssetStatsData = () => {
        return selectedAssets
            .filter(a => a.data)
            .map(asset => ({
                name: asset.ticker,
                return: Number((asset.data!.mean_return * 100).toFixed(2)),
                volatility: Number((asset.data!.volatility * 100).toFixed(2)),
            }));
    };

    // Filter unselected securities for dropdown
    const unselectedSecurities = availableSecurities.filter(
        s => !selectedAssets.some(a => a.ticker === s.ticker) && s.sector !== 'Bond'
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="text-2xl font-bold text-white">Portfolio Optimizer</h2>
                        <p className="text-slate-400 text-sm mt-1">
                            Build an optimal portfolio using Modern Portfolio Theory
                        </p>
                    </div>
                    {selectedAssets.length > 0 && (
                        <button
                            onClick={refreshAllData}
                            className="flex items-center gap-2 px-3 py-2 text-sm text-blue-400 hover:text-blue-300 border border-blue-400/30 rounded-lg hover:bg-blue-400/10 transition"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Refresh Data
                        </button>
                    )}
                </div>

                {/* Asset Selection */}
                <div className="mb-6">
                    <div className="flex items-center gap-4 mb-3">
                        <label className="text-sm font-medium text-slate-300">Add Assets to Portfolio:</label>
                        {loadingSecurities ? (
                            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                        ) : (
                            <select
                                onChange={(e) => {
                                    const sec = availableSecurities.find(s => s.ticker === e.target.value);
                                    if (sec) addAsset(sec);
                                    e.target.value = '';
                                }}
                                className="flex-1 max-w-xs bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400 [&>option]:bg-slate-800 [&>option]:text-white"
                                defaultValue=""
                            >
                                <option value="" disabled>Select a security...</option>
                                {unselectedSecurities.map(s => (
                                    <option key={s.ticker} value={s.ticker}>
                                        {s.ticker} - {s.name}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    {/* Selected Assets Grid */}
                    {selectedAssets.length === 0 ? (
                        <div className="text-center py-8 border border-dashed border-white/20 rounded-xl">
                            <Plus className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                            <p className="text-slate-400">No assets selected</p>
                            <p className="text-slate-500 text-sm">Add at least 2 assets to optimize</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {selectedAssets.map((asset, idx) => (
                                <div key={asset.ticker} className={`p-4 rounded-xl border transition ${asset.error
                                        ? 'bg-red-500/10 border-red-500/30'
                                        : asset.loaded
                                            ? 'bg-green-500/10 border-green-500/30'
                                            : 'bg-white/5 border-white/10'
                                    }`}>
                                    <div className="flex items-start justify-between mb-2">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-white font-semibold">{asset.ticker}</span>
                                                {asset.loading && <Loader2 className="w-3 h-3 animate-spin text-blue-400" />}
                                                {asset.loaded && !asset.error && <CheckCircle className="w-3 h-3 text-green-400" />}
                                            </div>
                                            <p className="text-xs text-slate-400 truncate max-w-[150px]">{asset.name}</p>
                                        </div>
                                        <button
                                            onClick={() => removeAsset(asset.ticker)}
                                            className="text-red-400 hover:text-red-300 p-1"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>

                                    {asset.error ? (
                                        <p className="text-xs text-red-300">{asset.error}</p>
                                    ) : asset.data ? (
                                        <div className="flex gap-4 text-xs">
                                            <div>
                                                <span className="text-slate-500">Return:</span>
                                                <span className={`ml-1 font-medium ${asset.data.mean_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {(asset.data.mean_return * 100).toFixed(2)}%
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-slate-500">Vol:</span>
                                                <span className="ml-1 text-orange-400 font-medium">
                                                    {(asset.data.volatility * 100).toFixed(2)}%
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-slate-500">Periods:</span>
                                                <span className="ml-1 text-slate-300">{asset.data.periods}</span>
                                            </div>
                                        </div>
                                    ) : null}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Optimization Settings */}
                <form onSubmit={handleOptimize} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Objective */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Optimization Objective
                            </label>
                            <select
                                value={objective}
                                onChange={(e) => setObjective(e.target.value as typeof objective)}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400 [&>option]:bg-slate-800"
                            >
                                <option value="max_sharpe">Maximize Sharpe Ratio</option>
                                <option value="min_vol">Minimize Volatility</option>
                                <option value="equal_weight">Equal Weight</option>
                            </select>
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
                                step="0.5"
                                min="0"
                                max="50"
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400"
                            />
                        </div>

                        {/* Lookback Period */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Lookback Period (weeks)
                            </label>
                            <select
                                value={lookbackPeriods}
                                onChange={(e) => setLookbackPeriods(parseInt(e.target.value))}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400 [&>option]:bg-slate-800"
                            >
                                <option value="13">3 Months (13 weeks)</option>
                                <option value="26">6 Months (26 weeks)</option>
                                <option value="52">1 Year (52 weeks)</option>
                                <option value="104">2 Years (104 weeks)</option>
                            </select>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={optimizing || !canOptimize}
                        className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold py-3 rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
                    >
                        {optimizing ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Optimizing Portfolio...
                            </>
                        ) : !canOptimize ? (
                            <>
                                <Info className="w-5 h-5" />
                                Add at least 2 assets with data
                            </>
                        ) : (
                            <>
                                <TrendingUp className="w-5 h-5" />
                                Optimize Portfolio ({readyAssets.length} assets)
                            </>
                        )}
                    </button>
                </form>

                {error && (
                    <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <span className="text-red-200 text-sm">{error}</span>
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
                            <div className="text-xs text-slate-500">Annualized</div>
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Portfolio Volatility</div>
                            <div className="text-2xl font-bold text-orange-400">
                                {(result.volatility * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-slate-500">Annualized Std Dev</div>
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Sharpe Ratio</div>
                            <div className="text-2xl font-bold text-blue-400">
                                {result.sharpe_ratio.toFixed(3)}
                            </div>
                            <div className="text-xs text-slate-500">Risk-adjusted return</div>
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-1">Strategy</div>
                            <div className="text-lg font-bold text-purple-400">
                                {objective === 'max_sharpe' ? 'Max Sharpe' : objective === 'min_vol' ? 'Min Vol' : 'Equal'}
                            </div>
                            <div className="text-xs text-slate-500">{readyAssets.length} assets</div>
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
                        <button
                            onClick={() => setActiveTab('stats')}
                            className={`px-4 py-2 font-medium border-b-2 transition ${activeTab === 'stats'
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            Asset Statistics
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
                                <div className="h-72">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={getWeightPieData()}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, value }) => `${name}: ${value}%`}
                                                outerRadius={100}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {getWeightPieData().map((_, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip formatter={(value: number) => `${value}%`} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="space-y-3">
                                    {Object.entries(result.weights)
                                        .sort(([, a], [, b]) => b - a)
                                        .map(([ticker, weight], idx) => (
                                            <div key={ticker} className="bg-white/5 rounded-lg p-3 flex justify-between items-center">
                                                <div className="flex items-center gap-3">
                                                    <div
                                                        className="w-3 h-3 rounded-full"
                                                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                                                    />
                                                    <span className="font-semibold text-white">{ticker}</span>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-lg font-bold text-emerald-400">
                                                        {(weight * 100).toFixed(1)}%
                                                    </div>
                                                    <div className="w-24 bg-white/10 rounded-full h-2 mt-1 overflow-hidden">
                                                        <div
                                                            className="h-full bg-gradient-to-r from-emerald-500 to-green-400"
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

                    {/* Frontier Chart */}
                    {activeTab === 'frontier' && frontierData && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                            <h3 className="text-lg font-semibold text-white mb-6">Efficient Frontier</h3>
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis
                                            dataKey="volatility"
                                            name="Volatility (%)"
                                            stroke="#94a3b8"
                                            label={{ value: 'Volatility (%)', position: 'bottom', fill: '#94a3b8' }}
                                        />
                                        <YAxis
                                            dataKey="return"
                                            name="Return (%)"
                                            stroke="#94a3b8"
                                            label={{ value: 'Return (%)', angle: -90, position: 'left', fill: '#94a3b8' }}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: number) => `${value.toFixed(2)}%`}
                                        />
                                        <Scatter
                                            name="Frontier"
                                            data={getFrontierChartData()}
                                            fill="#10b981"
                                            line
                                        />
                                        {/* Optimal portfolio point */}
                                        <Scatter
                                            name="Your Portfolio"
                                            data={[{
                                                volatility: Number((result.volatility * 100).toFixed(2)),
                                                return: Number((result.expected_return * 100).toFixed(2)),
                                            }]}
                                            fill="#fbbf24"
                                            shape="star"
                                        />
                                    </ScatterChart>
                                </ResponsiveContainer>
                            </div>
                            <p className="text-center text-sm text-slate-400 mt-4">
                                ⭐ Yellow star shows your optimized portfolio position
                            </p>
                        </div>
                    )}

                    {/* Asset Statistics */}
                    {activeTab === 'stats' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                            <h3 className="text-lg font-semibold text-white mb-6">Individual Asset Statistics</h3>
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={getAssetStatsData()} layout="vertical" margin={{ left: 50 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis type="number" stroke="#94a3b8" />
                                        <YAxis type="category" dataKey="name" stroke="#94a3b8" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: number) => `${value.toFixed(2)}%`}
                                        />
                                        <Legend />
                                        <Bar dataKey="return" name="Weekly Return %" fill="#10b981" />
                                        <Bar dataKey="volatility" name="Weekly Vol %" fill="#f59e0b" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
