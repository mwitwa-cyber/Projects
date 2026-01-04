import { useState, useEffect } from 'react';
import {
    TrendingUp, Loader2, AlertCircle, RefreshCw, BarChart2, LineChart,
    Target
} from 'lucide-react';
import { YieldCurveChart } from './charts/YieldCurveChart';
import { CandlestickChart } from './charts/CandlestickChart';
import { analyticsService } from '../services/analytics';
import api from '../services/api';
import type { YieldCurveResponse, OHLCData, CAPMResponse } from '../types/analytics';

// LuSE Securities with IDs for risk analysis
const SECURITIES = [
    { ticker: 'ZCCM', name: 'ZCCM-IH', id: 34, sector: 'Mining' },
    { ticker: 'ATEL', name: 'Airtel Zambia', id: 36, sector: 'Telecom' },
    { ticker: 'SCBL', name: 'Standard Chartered', id: 38, sector: 'Banking' },
    { ticker: 'ZNCO', name: 'Zanaco Bank', id: 39, sector: 'Banking' },
    { ticker: 'CECZ', name: 'Copperbelt Energy', id: 43, sector: 'Energy' },
    { ticker: 'BATA', name: 'Bata Shoe', id: 47, sector: 'Consumer' },
];

const BENCHMARK_ID = 34; // ZCCM as market proxy

interface RiskMetrics {
    beta: number;
    var_95: number;
    cvar_95: number;
    volatility_annual: number;
}

export const AdvancedAnalytics = () => {
    // State
    const [selectedTicker, setSelectedTicker] = useState('ZNCO');
    const [yieldData, setYieldData] = useState<YieldCurveResponse | null>(null);
    const [ohlcData, setOhlcData] = useState<OHLCData[] | null>(null);
    const [capmData, setCapmData] = useState<CAPMResponse | null>(null);
    const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadingStock, setLoadingStock] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'yield' | 'price' | 'risk'>('yield');

    // Initial data load
    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            // Load yield curve
            try {
                const yc = await analyticsService.getYieldCurve();
                setYieldData(yc);
            } catch (e) {
                console.error('Yield curve unavailable', e);
            }

            // Load default stock
            await loadStockData(selectedTicker);
            setError(null);
        } catch (err) {
            setError('Failed to load analytics data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const loadStockData = async (ticker: string) => {
        setLoadingStock(true);
        try {
            const [ohlc, capm] = await Promise.all([
                analyticsService.getOHLC(ticker, 90),
                analyticsService.getCAPM(ticker).catch(() => null)
            ]);
            setOhlcData(ohlc);
            setCapmData(capm);

            // Load risk metrics from TimescaleDB endpoint
            const security = SECURITIES.find(s => s.ticker === ticker);
            if (security) {
                try {
                    const riskResponse = await api.get(`/analytics/timescale/risk/${security.id}`, {
                        params: {
                            benchmark_id: BENCHMARK_ID,
                            lookback_weeks: 52
                        }
                    });
                    setRiskMetrics(riskResponse.data);
                } catch (e) {
                    console.error('Risk metrics unavailable');
                    setRiskMetrics(null);
                }
            }
        } catch (e) {
            console.error('Failed to load stock data', e);
        } finally {
            setLoadingStock(false);
        }
    };

    const handleTickerChange = async (ticker: string) => {
        setSelectedTicker(ticker);
        await loadStockData(ticker);
    };



    if (loading) {
        return (
            <div className="flex items-center justify-center py-20 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin mr-3" />
                Loading Advanced Analytics...
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
                            <TrendingUp className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">Advanced Analytics</h2>
                            <p className="text-slate-400 text-sm">Yield curves, OHLC charts & quantitative risk models</p>
                        </div>
                    </div>
                    <button
                        onClick={loadInitialData}
                        className="flex items-center gap-2 px-3 py-2 border border-white/20 rounded-lg text-slate-300 hover:bg-white/5 transition"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>

                {/* Security Quick Select */}
                <div className="mb-4">
                    <label className="block text-sm font-medium text-slate-300 mb-3">
                        Select Security for Analysis
                    </label>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                        {SECURITIES.map(sec => (
                            <button
                                key={sec.ticker}
                                onClick={() => handleTickerChange(sec.ticker)}
                                className={`p-3 rounded-lg border transition text-left ${selectedTicker === sec.ticker
                                    ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                                    : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                                    }`}
                            >
                                <div className="font-semibold text-sm">{sec.ticker}</div>
                                <div className="text-xs text-slate-500">{sec.sector}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 border-b border-white/10">
                    <button
                        onClick={() => setActiveTab('yield')}
                        className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'yield'
                            ? 'border-indigo-500 text-indigo-400'
                            : 'border-transparent text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        <LineChart className="w-4 h-4" />
                        Yield Curve
                    </button>
                    <button
                        onClick={() => setActiveTab('price')}
                        className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'price'
                            ? 'border-indigo-500 text-indigo-400'
                            : 'border-transparent text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        <BarChart2 className="w-4 h-4" />
                        Price Action
                    </button>
                    <button
                        onClick={() => setActiveTab('risk')}
                        className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'risk'
                            ? 'border-indigo-500 text-indigo-400'
                            : 'border-transparent text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        <Target className="w-4 h-4" />
                        Risk Analysis
                    </button>
                </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'yield' && (
                <div className="space-y-6">
                    {/* Yield Curve Card */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <LineChart className="w-5 h-5 text-blue-400" />
                                GRZ Treasury Yield Curve
                            </h3>
                            {yieldData?.parameters && (
                                <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                                    Nelson-Siegel Model
                                </span>
                            )}
                        </div>

                        {yieldData ? (
                            <>
                                <div className="h-80">
                                    <YieldCurveChart
                                        curveData={yieldData.curve}
                                        observedData={yieldData.observed}
                                        parameters={yieldData.parameters}
                                    />
                                </div>

                                {/* Parameters Display */}
                                {yieldData.parameters && (
                                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="bg-white/5 rounded-lg p-3">
                                            <div className="text-xs text-slate-400">β₀ (Level)</div>
                                            <div className="text-lg font-bold text-white">
                                                {(yieldData.parameters.beta0 * 100).toFixed(2)}%
                                            </div>
                                        </div>
                                        <div className="bg-white/5 rounded-lg p-3">
                                            <div className="text-xs text-slate-400">β₁ (Slope)</div>
                                            <div className="text-lg font-bold text-white">
                                                {(yieldData.parameters.beta1 * 100).toFixed(2)}%
                                            </div>
                                        </div>
                                        <div className="bg-white/5 rounded-lg p-3">
                                            <div className="text-xs text-slate-400">β₂ (Curvature)</div>
                                            <div className="text-lg font-bold text-white">
                                                {(yieldData.parameters.beta2 * 100).toFixed(2)}%
                                            </div>
                                        </div>
                                        <div className="bg-white/5 rounded-lg p-3">
                                            <div className="text-xs text-slate-400">λ (Lambda)</div>
                                            <div className="text-lg font-bold text-white">
                                                {yieldData.parameters.lambda.toFixed(2)}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="h-80 flex items-center justify-center text-slate-400">
                                <AlertCircle className="w-5 h-5 mr-2" />
                                Yield curve data unavailable
                            </div>
                        )}
                    </div>

                    {/* Explanation Card */}
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                        <h4 className="text-blue-300 font-semibold mb-2">About the Yield Curve</h4>
                        <p className="text-blue-200/80 text-sm">
                            The yield curve shows the relationship between government bond yields and their time to maturity.
                            This curve is fitted using the Nelson-Siegel model on GRZ (Government of Republic of Zambia) treasury bonds
                            ranging from 2-year to 15-year maturities. An inverted curve (short rates &gt; long rates)
                            historically signals economic slowdown.
                        </p>
                    </div>
                </div>
            )}

            {activeTab === 'price' && (
                <div className="space-y-6">
                    {/* Price Action Card */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <BarChart2 className="w-5 h-5 text-green-400" />
                                Price Action: {selectedTicker}
                                {loadingStock && <Loader2 className="w-4 h-4 animate-spin ml-2" />}
                            </h3>
                            <span className="text-xs text-slate-400">Last 90 days</span>
                        </div>

                        <div className="h-[450px]">
                            {ohlcData && ohlcData.length > 0 ? (
                                <CandlestickChart data={ohlcData} height={420} />
                            ) : (
                                <div className="h-full flex items-center justify-center text-slate-400">
                                    <AlertCircle className="w-5 h-5 mr-2" />
                                    No price data available for {selectedTicker}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* CAPM Stats */}
                    {capmData && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">Expected Return</div>
                                <div className="text-2xl font-bold text-green-400">
                                    {(capmData.expected_return * 100).toFixed(2)}%
                                </div>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">Beta (β)</div>
                                <div className="text-2xl font-bold text-blue-400">
                                    {capmData.beta.toFixed(3)}
                                </div>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">Risk Premium</div>
                                <div className="text-2xl font-bold text-purple-400">
                                    {((capmData.expected_return - 0.20) * 100).toFixed(2)}%
                                </div>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">Alpha (vs Market)</div>
                                <div className={`text-2xl font-bold ${capmData.alpha >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {(capmData.alpha * 100).toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'risk' && (
                <div className="space-y-6">
                    {/* Risk Metrics Cards */}
                    {riskMetrics ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">Beta (β)</div>
                                <div className={`text-2xl font-bold ${riskMetrics.beta > 1 ? 'text-red-400' : riskMetrics.beta < 0.8 ? 'text-green-400' : 'text-yellow-400'
                                    }`}>
                                    {riskMetrics.beta.toFixed(3)}
                                </div>
                                <div className="text-xs text-slate-500 mt-1">
                                    {riskMetrics.beta > 1 ? 'High volatility' : 'Defensive'}
                                </div>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">VaR (95%)</div>
                                <div className="text-2xl font-bold text-red-400">
                                    {(riskMetrics.var_95 * 100).toFixed(2)}%
                                </div>
                                <div className="text-xs text-slate-500 mt-1">Max weekly loss</div>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">CVaR (95%)</div>
                                <div className="text-2xl font-bold text-orange-400">
                                    {(riskMetrics.cvar_95 * 100).toFixed(2)}%
                                </div>
                                <div className="text-xs text-slate-500 mt-1">Expected shortfall</div>
                            </div>
                            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <div className="text-xs text-slate-400 mb-1">Annual Volatility</div>
                                <div className="text-2xl font-bold text-yellow-400">
                                    {(riskMetrics.volatility_annual * 100).toFixed(2)}%
                                </div>
                                <div className="text-xs text-slate-500 mt-1">Std dev (annualized)</div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-yellow-400" />
                            <span className="text-yellow-200 text-sm">
                                Risk metrics require TimescaleDB functions. Showing CAPM-based analysis instead.
                            </span>
                        </div>
                    )}

                    {/* Risk Interpretation */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Target className="w-5 h-5 text-purple-400" />
                            Risk Interpretation: {selectedTicker}
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                    <h4 className="text-blue-300 font-medium mb-2">Systematic Risk (Beta)</h4>
                                    <p className="text-blue-200/80 text-sm">
                                        {riskMetrics?.beta !== undefined ? (
                                            riskMetrics.beta > 1
                                                ? `${selectedTicker} is ${((riskMetrics.beta - 1) * 100).toFixed(0)}% more volatile than the market. It amplifies both gains and losses.`
                                                : riskMetrics.beta < 0.8
                                                    ? `${selectedTicker} is defensive, moving ${((1 - riskMetrics.beta) * 100).toFixed(0)}% less than the market.`
                                                    : `${selectedTicker} moves roughly in line with the market.`
                                        ) : (
                                            capmData ? `Beta from CAPM: ${capmData.beta.toFixed(3)}` : 'No beta data available'
                                        )}
                                    </p>
                                </div>

                                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                                    <h4 className="text-red-300 font-medium mb-2">Value at Risk</h4>
                                    <p className="text-red-200/80 text-sm">
                                        {riskMetrics?.var_95 !== undefined
                                            ? `With 95% confidence, weekly losses won't exceed ${(riskMetrics.var_95 * 100).toFixed(2)}%.`
                                            : 'VaR data requires TimescaleDB risk functions.'}
                                    </p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                                    <h4 className="text-orange-300 font-medium mb-2">Tail Risk (CVaR)</h4>
                                    <p className="text-orange-200/80 text-sm">
                                        {riskMetrics?.cvar_95 !== undefined
                                            ? `In worst-case scenarios (5% of weeks), average loss is ${(riskMetrics.cvar_95 * 100).toFixed(2)}%.`
                                            : 'CVaR data requires TimescaleDB risk functions.'}
                                    </p>
                                </div>

                                <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                                    <h4 className="text-purple-300 font-medium mb-2">Methodology</h4>
                                    <p className="text-purple-200/80 text-sm">
                                        Risk metrics calculated using 52-week rolling window. Beta regressed against ZCCM as market proxy.
                                        VaR uses historical simulation.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                    <span className="text-red-200">{error}</span>
                </div>
            )}
        </div>
    );
};
