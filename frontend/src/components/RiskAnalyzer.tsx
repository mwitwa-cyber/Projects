import { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Loader2, AlertCircle, TrendingDown, TrendingUp, Shield, Activity,
    BarChart3, Target, RefreshCw, Zap, Info, ChevronDown, CheckCircle
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, LineChart, Line, ScatterChart, Scatter,
    AreaChart, Area, Cell, ReferenceLine
} from 'recharts';
import api, { riskAPI, optimizationAPI } from '../services/api';

// LuSE Stock Presets for quick analysis
const LUSE_PRESETS = [
    { ticker: 'ZCCM', name: 'ZCCM-IH', sector: 'Mining' },
    { ticker: 'ATEL', name: 'Airtel Zambia', sector: 'Telecom' },
    { ticker: 'CECZ', name: 'Copperbelt Energy', sector: 'Energy' },
    { ticker: 'ZNCO', name: 'Zanaco Bank', sector: 'Banking' },
    { ticker: 'ZSUG', name: 'Zambia Sugar', sector: 'Consumer' },
    { ticker: 'ZMBF', name: 'Zambeef', sector: 'Agriculture' },
];

// Market benchmark (LASI proxy - use ZCCM as it's the largest)
const MARKET_BENCHMARK = 'ZCCM';

interface SecurityInfo {
    ticker: string;
    name: string;
    sector?: string;
}

interface ReturnsData {
    ticker: string;
    returns: number[];
    periods: number;
    mean_return: number;
    volatility: number;
}

interface RiskMetrics {
    var_95: number;
    var_99: number;
    cvar_95: number;
    volatility: number;
    max_drawdown: number;
    sharpe_ratio: number;
}

interface BetaResult {
    beta: number;
    alpha: number;
    r_squared: number;
    correlation: number;
}

export const RiskAnalyzer = () => {
    // State
    const [availableSecurities, setAvailableSecurities] = useState<SecurityInfo[]>([]);
    const [loadingSecurities, setLoadingSecurities] = useState(true);

    // Selected asset for analysis
    const [selectedTicker, setSelectedTicker] = useState<string>('');
    const [assetData, setAssetData] = useState<ReturnsData | null>(null);
    const [marketData, setMarketData] = useState<ReturnsData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Results
    const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
    const [betaResult, setBetaResult] = useState<BetaResult | null>(null);
    const [analyzing, setAnalyzing] = useState(false);

    // Settings
    const [lookbackWeeks, setLookbackWeeks] = useState(52);
    const [confidenceLevel, setConfidenceLevel] = useState(0.95);

    // UI
    const [activeTab, setActiveTab] = useState<'overview' | 'var' | 'beta' | 'distribution'>('overview');

    // Fetch available securities
    useEffect(() => {
        const fetchSecurities = async () => {
            try {
                const response = await api.get('/market-data/securities');
                setAvailableSecurities(response.data.filter((s: SecurityInfo) =>
                    s.sector !== 'Bond' && s.sector !== 'Fixed Income'
                ));
            } catch (err) {
                console.error('Failed to fetch securities', err);
            } finally {
                setLoadingSecurities(false);
            }
        };
        fetchSecurities();
    }, []);

    // Fetch returns data for a ticker
    const fetchReturnsData = async (ticker: string): Promise<ReturnsData | null> => {
        try {
            const response = await api.get(`/market-data/returns/${ticker}`, {
                params: { periods: lookbackWeeks }
            });
            return response.data;
        } catch {
            return null;
        }
    };

    // Calculate VaR and CVaR locally from returns
    const calculateVaRMetrics = useMemo(() => {
        if (!assetData || assetData.returns.length < 10) return null;

        const returns = [...assetData.returns].sort((a, b) => a - b);
        const n = returns.length;

        // Historical VaR
        const var95Index = Math.floor(n * 0.05);
        const var99Index = Math.floor(n * 0.01);
        const var_95 = Math.abs(returns[var95Index] || 0);
        const var_99 = Math.abs(returns[var99Index] || 0);

        // CVaR (Expected Shortfall) - average of returns below VaR
        const tailReturns95 = returns.slice(0, var95Index + 1);
        const cvar_95 = Math.abs(tailReturns95.reduce((a, b) => a + b, 0) / tailReturns95.length || 0);

        // Volatility (already calculated)
        const volatility = assetData.volatility;

        // Max Drawdown (simplified - peak to trough)
        let peak = 0;
        let maxDrawdown = 0;
        let cumReturn = 0;
        for (const r of assetData.returns) {
            cumReturn += r;
            if (cumReturn > peak) peak = cumReturn;
            const drawdown = peak - cumReturn;
            if (drawdown > maxDrawdown) maxDrawdown = drawdown;
        }

        // Sharpe Ratio (assuming 20% risk-free rate, weekly)
        const weeklyRf = 0.20 / 52;
        const sharpe_ratio = volatility > 0
            ? (assetData.mean_return - weeklyRf) / volatility
            : 0;

        return {
            var_95,
            var_99,
            cvar_95,
            volatility,
            max_drawdown: maxDrawdown,
            sharpe_ratio,
        };
    }, [assetData]);

    // Calculate Beta locally
    const calculateBetaMetrics = useMemo(() => {
        if (!assetData || !marketData || assetData.returns.length < 10) return null;

        // Align returns to same length
        const minLen = Math.min(assetData.returns.length, marketData.returns.length);
        const assetReturns = assetData.returns.slice(-minLen);
        const marketReturns = marketData.returns.slice(-minLen);

        // Calculate means
        const assetMean = assetReturns.reduce((a, b) => a + b, 0) / minLen;
        const marketMean = marketReturns.reduce((a, b) => a + b, 0) / minLen;

        // Calculate covariance and variance
        let covariance = 0;
        let marketVariance = 0;
        let assetVariance = 0;

        for (let i = 0; i < minLen; i++) {
            const assetDev = assetReturns[i] - assetMean;
            const marketDev = marketReturns[i] - marketMean;
            covariance += assetDev * marketDev;
            marketVariance += marketDev * marketDev;
            assetVariance += assetDev * assetDev;
        }

        covariance /= minLen;
        marketVariance /= minLen;
        assetVariance /= minLen;

        const beta = marketVariance > 0 ? covariance / marketVariance : 0;
        const alpha = assetMean - (beta * marketMean);
        const correlation = marketVariance > 0 && assetVariance > 0
            ? covariance / (Math.sqrt(marketVariance) * Math.sqrt(assetVariance))
            : 0;
        const r_squared = correlation * correlation;

        return { beta, alpha, r_squared, correlation };
    }, [assetData, marketData]);

    // Handle security selection
    const handleSelectSecurity = async (ticker: string) => {
        if (!ticker) return;

        setSelectedTicker(ticker);
        setLoading(true);
        setError('');
        setAssetData(null);
        setMarketData(null);
        setRiskMetrics(null);
        setBetaResult(null);

        try {
            // Fetch asset returns
            const asset = await fetchReturnsData(ticker);
            if (!asset || asset.periods < 10) {
                setError(`Insufficient data for ${ticker}. Need at least 10 periods.`);
                setLoading(false);
                return;
            }
            setAssetData(asset);

            // Fetch market benchmark returns
            if (ticker !== MARKET_BENCHMARK) {
                const market = await fetchReturnsData(MARKET_BENCHMARK);
                setMarketData(market);
            }

            setActiveTab('overview');
        } catch (err) {
            setError('Failed to fetch security data');
        } finally {
            setLoading(false);
        }
    };

    // Get distribution chart data
    const getDistributionData = useMemo(() => {
        if (!assetData) return [];

        const returns = assetData.returns;
        const min = Math.min(...returns);
        const max = Math.max(...returns);
        const binCount = 15;
        const binWidth = (max - min) / binCount || 0.01;

        const bins: { range: string; count: number; value: number }[] = [];

        for (let i = 0; i < binCount; i++) {
            const binStart = min + i * binWidth;
            const binEnd = binStart + binWidth;
            const count = returns.filter(r => r >= binStart && r < binEnd).length;
            bins.push({
                range: `${(binStart * 100).toFixed(1)}%`,
                count,
                value: (binStart + binEnd) / 2,
            });
        }

        return bins;
    }, [assetData]);

    // Get scatter plot data for beta regression
    const getScatterData = useMemo(() => {
        if (!assetData || !marketData) return [];

        const minLen = Math.min(assetData.returns.length, marketData.returns.length);
        const data = [];

        for (let i = 0; i < minLen; i++) {
            data.push({
                market: marketData.returns[i] * 100,
                asset: assetData.returns[i] * 100,
            });
        }

        return data;
    }, [assetData, marketData]);

    // Get time series data
    const getTimeSeriesData = useMemo(() => {
        if (!assetData) return [];

        return assetData.returns.map((r, i) => ({
            period: i + 1,
            return: r * 100,
            cumulative: assetData.returns.slice(0, i + 1).reduce((a, b) => a + b, 0) * 100,
        }));
    }, [assetData]);

    // Get risk level color and label
    const getRiskLevel = (beta: number) => {
        if (beta < 0.8) return { color: 'text-green-400', bg: 'bg-green-500/20', label: 'Low Risk' };
        if (beta < 1.2) return { color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'Moderate' };
        return { color: 'text-red-400', bg: 'bg-red-500/20', label: 'High Risk' };
    };

    return (
        <div className="space-y-6">
            {/* Header & Controls */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-r from-red-500 to-orange-600 rounded-lg">
                            <Shield className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">Risk Analytics</h2>
                            <p className="text-slate-400 text-sm">VaR, CVaR, Beta & Volatility Analysis</p>
                        </div>
                    </div>
                </div>

                {/* Quick Select Presets */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-300 mb-3">
                        Quick Select: Popular LuSE Securities
                    </label>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                        {LUSE_PRESETS.map(preset => (
                            <button
                                key={preset.ticker}
                                onClick={() => handleSelectSecurity(preset.ticker)}
                                className={`p-3 rounded-lg border transition text-left ${selectedTicker === preset.ticker
                                        ? 'bg-red-500/20 border-red-500/50 text-red-300'
                                        : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                                    }`}
                            >
                                <div className="font-semibold text-sm">{preset.ticker}</div>
                                <div className="text-xs text-slate-500">{preset.sector}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Security Selection */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Select Security
                        </label>
                        {loadingSecurities ? (
                            <div className="flex items-center gap-2 text-slate-400">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Loading...
                            </div>
                        ) : (
                            <select
                                value={selectedTicker}
                                onChange={(e) => handleSelectSecurity(e.target.value)}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-red-400 [&>option]:bg-slate-800"
                            >
                                <option value="">Select a security...</option>
                                {availableSecurities.map(s => (
                                    <option key={s.ticker} value={s.ticker}>
                                        {s.ticker} - {s.name}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Lookback Period
                        </label>
                        <select
                            value={lookbackWeeks}
                            onChange={(e) => setLookbackWeeks(parseInt(e.target.value))}
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-red-400 [&>option]:bg-slate-800"
                        >
                            <option value={26}>6 Months (26 weeks)</option>
                            <option value={52}>1 Year (52 weeks)</option>
                            <option value={104}>2 Years (104 weeks)</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Confidence Level
                        </label>
                        <div className="flex gap-2">
                            {[0.90, 0.95, 0.99].map(level => (
                                <button
                                    key={level}
                                    onClick={() => setConfidenceLevel(level)}
                                    className={`flex-1 py-2 px-3 rounded-lg font-medium text-sm transition ${confidenceLevel === level
                                            ? 'bg-red-500/30 border border-red-500 text-red-300'
                                            : 'bg-white/10 border border-white/20 text-slate-300 hover:bg-white/15'
                                        }`}
                                >
                                    {(level * 100).toFixed(0)}%
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="flex items-center justify-center py-8 text-slate-400">
                        <Loader2 className="w-6 h-6 animate-spin mr-2" />
                        Fetching historical data...
                    </div>
                )}

                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <span className="text-red-200 text-sm">{error}</span>
                    </div>
                )}
            </div>

            {/* Results */}
            {assetData && calculateVaRMetrics && (
                <div className="space-y-6">
                    {/* Key Metrics Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-1">VaR (95%)</div>
                            <div className="text-2xl font-bold text-red-400">
                                {(calculateVaRMetrics.var_95 * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-slate-500">Max weekly loss</div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-1">CVaR (95%)</div>
                            <div className="text-2xl font-bold text-orange-400">
                                {(calculateVaRMetrics.cvar_95 * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-slate-500">Expected shortfall</div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-1">Volatility</div>
                            <div className="text-2xl font-bold text-yellow-400">
                                {(calculateVaRMetrics.volatility * 100).toFixed(2)}%
                            </div>
                            <div className="text-xs text-slate-500">Weekly std dev</div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-xs text-slate-400 mb-1">Sharpe Ratio</div>
                            <div className={`text-2xl font-bold ${calculateVaRMetrics.sharpe_ratio >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {calculateVaRMetrics.sharpe_ratio.toFixed(3)}
                            </div>
                            <div className="text-xs text-slate-500">Risk-adjusted</div>
                        </div>

                        {calculateBetaMetrics && (
                            <>
                                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                    <div className="text-xs text-slate-400 mb-1">Beta (β)</div>
                                    <div className={`text-2xl font-bold ${getRiskLevel(calculateBetaMetrics.beta).color}`}>
                                        {calculateBetaMetrics.beta.toFixed(3)}
                                    </div>
                                    <div className={`text-xs px-2 py-0.5 rounded inline-block mt-1 ${getRiskLevel(calculateBetaMetrics.beta).bg} ${getRiskLevel(calculateBetaMetrics.beta).color}`}>
                                        {getRiskLevel(calculateBetaMetrics.beta).label}
                                    </div>
                                </div>

                                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                    <div className="text-xs text-slate-400 mb-1">R² (Model Fit)</div>
                                    <div className="text-2xl font-bold text-purple-400">
                                        {(calculateBetaMetrics.r_squared * 100).toFixed(1)}%
                                    </div>
                                    <div className="text-xs text-slate-500">Explained variance</div>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-4 border-b border-white/10">
                        <button
                            onClick={() => setActiveTab('overview')}
                            className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'overview'
                                    ? 'border-red-500 text-red-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            <Activity className="w-4 h-4" />
                            Return Series
                        </button>
                        <button
                            onClick={() => setActiveTab('distribution')}
                            className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'distribution'
                                    ? 'border-red-500 text-red-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            <BarChart3 className="w-4 h-4" />
                            Distribution
                        </button>
                        <button
                            onClick={() => setActiveTab('var')}
                            className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'var'
                                    ? 'border-red-500 text-red-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            <TrendingDown className="w-4 h-4" />
                            VaR Analysis
                        </button>
                        {calculateBetaMetrics && (
                            <button
                                onClick={() => setActiveTab('beta')}
                                className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'beta'
                                        ? 'border-red-500 text-red-400'
                                        : 'border-transparent text-slate-400 hover:text-slate-300'
                                    }`}
                            >
                                <Target className="w-4 h-4" />
                                Beta Regression
                            </button>
                        )}
                    </div>

                    {/* Overview Tab */}
                    {activeTab === 'overview' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">
                                Weekly Returns - {selectedTicker}
                            </h3>
                            <div className="h-72">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={getTimeSeriesData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="period" stroke="#94a3b8" />
                                        <YAxis stroke="#94a3b8" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: number) => [`${value.toFixed(2)}%`]}
                                        />
                                        <Legend />
                                        <Area
                                            type="monotone"
                                            dataKey="return"
                                            name="Weekly Return"
                                            stroke="#3b82f6"
                                            fill="#3b82f633"
                                        />
                                        <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* Distribution Tab */}
                    {activeTab === 'distribution' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">
                                Return Distribution (Histogram)
                            </h3>
                            <div className="h-72">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={getDistributionData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="range" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                                        <YAxis stroke="#94a3b8" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                        />
                                        <Bar dataKey="count" name="Frequency">
                                            {getDistributionData.map((entry, index) => (
                                                <Cell
                                                    key={`cell-${index}`}
                                                    fill={entry.value < 0 ? '#ef4444' : '#10b981'}
                                                />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <p className="text-center text-sm text-slate-400 mt-4">
                                Red bars = negative returns | Green bars = positive returns
                            </p>
                        </div>
                    )}

                    {/* VaR Tab */}
                    {activeTab === 'var' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-6">Value at Risk Analysis</h3>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <TrendingDown className="w-5 h-5 text-red-400" />
                                            <span className="text-red-300 font-semibold">VaR Interpretation</span>
                                        </div>
                                        <p className="text-sm text-slate-300">
                                            With 95% confidence, the maximum weekly loss for <strong>{selectedTicker}</strong> is
                                            <span className="text-red-400 font-bold"> {(calculateVaRMetrics.var_95 * 100).toFixed(2)}%</span>.
                                        </p>
                                        <p className="text-sm text-slate-300 mt-2">
                                            In other words, there's only a 5% chance of losing more than this in any given week.
                                        </p>
                                    </div>

                                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <AlertCircle className="w-5 h-5 text-orange-400" />
                                            <span className="text-orange-300 font-semibold">CVaR (Expected Shortfall)</span>
                                        </div>
                                        <p className="text-sm text-slate-300">
                                            If losses exceed VaR, the expected average loss is
                                            <span className="text-orange-400 font-bold"> {(calculateVaRMetrics.cvar_95 * 100).toFixed(2)}%</span>.
                                        </p>
                                    </div>
                                </div>

                                <div className="bg-white/5 rounded-lg p-4">
                                    <h4 className="font-semibold text-white mb-4">Risk Metrics Summary</h4>
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">VaR (90%)</span>
                                            <span className="text-white font-medium">
                                                {(assetData.returns.sort((a, b) => a - b)[Math.floor(assetData.returns.length * 0.1)] * -100).toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">VaR (95%)</span>
                                            <span className="text-red-400 font-medium">
                                                {(calculateVaRMetrics.var_95 * 100).toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">VaR (99%)</span>
                                            <span className="text-red-500 font-medium">
                                                {(calculateVaRMetrics.var_99 * 100).toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between border-t border-white/10 pt-3 mt-3">
                                            <span className="text-slate-400">Weekly Volatility</span>
                                            <span className="text-yellow-400 font-medium">
                                                {(calculateVaRMetrics.volatility * 100).toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Annualized Volatility</span>
                                            <span className="text-yellow-400 font-medium">
                                                {(calculateVaRMetrics.volatility * Math.sqrt(52) * 100).toFixed(2)}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Beta Tab */}
                    {activeTab === 'beta' && calculateBetaMetrics && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">
                                Beta Regression: {selectedTicker} vs {MARKET_BENCHMARK}
                            </h3>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="h-72">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis
                                                dataKey="market"
                                                name="Market Return"
                                                stroke="#94a3b8"
                                                label={{ value: 'Market Return (%)', position: 'bottom', fill: '#94a3b8' }}
                                            />
                                            <YAxis
                                                dataKey="asset"
                                                name="Asset Return"
                                                stroke="#94a3b8"
                                                label={{ value: 'Asset Return (%)', angle: -90, position: 'left', fill: '#94a3b8' }}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                                formatter={(value: number) => `${value.toFixed(2)}%`}
                                            />
                                            <Scatter
                                                name={selectedTicker}
                                                data={getScatterData}
                                                fill="#3b82f6"
                                            />
                                        </ScatterChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="space-y-4">
                                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Target className="w-5 h-5 text-blue-400" />
                                            <span className="text-blue-300 font-semibold">Beta Interpretation</span>
                                        </div>
                                        <p className="text-sm text-slate-300">
                                            <strong>{selectedTicker}</strong> has a beta of <span className="text-blue-400 font-bold">{calculateBetaMetrics.beta.toFixed(3)}</span>
                                            {calculateBetaMetrics.beta > 1
                                                ? ', meaning it moves MORE than the market (amplifies gains/losses).'
                                                : calculateBetaMetrics.beta < 1
                                                    ? ', meaning it moves LESS than the market (defensive).'
                                                    : ', meaning it moves WITH the market.'}
                                        </p>
                                    </div>

                                    <div className="bg-white/5 rounded-lg p-4">
                                        <h4 className="font-semibold text-white mb-3">Regression Statistics</h4>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Beta (β)</span>
                                                <span className="text-blue-400 font-medium">{calculateBetaMetrics.beta.toFixed(4)}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Alpha (α)</span>
                                                <span className={`font-medium ${calculateBetaMetrics.alpha >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {(calculateBetaMetrics.alpha * 100).toFixed(4)}%
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">R²</span>
                                                <span className="text-purple-400 font-medium">{(calculateBetaMetrics.r_squared * 100).toFixed(2)}%</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Correlation</span>
                                                <span className="text-cyan-400 font-medium">{calculateBetaMetrics.correlation.toFixed(4)}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
