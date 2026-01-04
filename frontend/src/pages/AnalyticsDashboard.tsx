import { useState, useEffect } from 'react';
import { YieldCurveChart } from '../components/charts/YieldCurveChart';
import { CandlestickChart } from '../components/charts/CandlestickChart';
import { RiskProfileCard } from '../components/analytics/RiskProfileCard';
import { TimeScaleRiskCard } from '../components/analytics/TimeScaleRiskCard';
import { analyticsService } from '../services/analytics';
import type { YieldCurveResponse, OHLCData, CAPMResponse } from '../types/analytics';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle } from 'lucide-react';

// Temporary mapping until backend endpoints return IDs
const TICKER_MAP: Record<string, number> = {
    'ZNCO': 39,
    'MAFS': 40,
    'AECI': 33,
    'CECZ': 43,
    'ATEL': 36,
    'SCBL': 38,
    'BATA': 47,
    'SHOP': 54,
    'ZCCM': 34
};

const BENCHMARK_ID = 34; // ZCCM as benchmark

export const AnalyticsDashboard = () => {
    const navigate = useNavigate();
    // State
    const [ticker, setTicker] = useState('ZNCO');
    const [yieldData, setYieldData] = useState<YieldCurveResponse | null>(null);
    const [ohlcData, setOhlcData] = useState<OHLCData[] | null>(null);
    const [capmData, setCapmData] = useState<CAPMResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Initial Load (Yield Curve + Default Stock)
    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                // Fetch Yield Curve
                try {
                    const yc = await analyticsService.getYieldCurve();
                    setYieldData(yc);
                } catch (e) {
                    console.error("Failed to load yield curve", e);
                }

                // Fetch Stock Data
                await loadStockData(ticker);

                setError(null);
            } catch (err: any) {
                setError('Failed to load analytics data.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    // Load Stock Specific Data
    const loadStockData = async (sym: string) => {
        const [ohlc, capm] = await Promise.all([
            analyticsService.getOHLC(sym, 90), // Last 90 days candles
            analyticsService.getCAPM(sym)
        ]);
        setOhlcData(ohlc);
        setCapmData(capm);
    };

    const handleTickerChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newTicker = e.target.value;
        setTicker(newTicker);
        setLoading(true);
        try {
            await loadStockData(newTicker);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !yieldData) return <div className="min-h-screen bg-fintech-bg p-8 text-center text-white">Loading Analytics...</div>;
    if (error) return <div className="min-h-screen bg-fintech-bg p-8 text-center text-red-400">Error: {error}</div>;

    return (
        <div className="min-h-screen bg-fintech-bg p-6 space-y-8 animate-fade-in">
            <div className="flex items-center gap-4">
                <button
                    onClick={() => navigate('/')}
                    className="p-2 bg-fintech-card border border-white/10 rounded-lg text-slate-400 hover:text-white hover:border-white/30 transition-colors"
                    title="Back to Dashboard"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div className="flex-1 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-white">Advanced Analytics</h1>
                        <p className="text-slate-400">Quantitative modeling and risk assessment</p>
                    </div>

                    {/* Simple Ticker Selector */}
                    <select
                        value={ticker}
                        onChange={handleTickerChange}
                        className="p-2 border border-white/20 rounded-md shadow-sm bg-fintech-card text-white"
                    >
                        {Object.keys(TICKER_MAP).map(t => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Section 1: Macro (Yield Curve) */}
            <section>
                <div className="mb-4 flex items-center gap-2">
                    <h2 className="text-xl font-semibold text-white">Macro: Yield Curve</h2>
                    {yieldData?.parameters && <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">Nelson-Siegel Fit</span>}
                </div>
                {yieldData ? (
                    <YieldCurveChart
                        curveData={yieldData.curve}
                        observedData={yieldData.observed}
                        parameters={yieldData.parameters}
                    />
                ) : (
                    <div className="h-64 bg-white/5 rounded flex items-center justify-center text-slate-400">
                        Yield Curve Data Unavailable
                    </div>
                )}
            </section>

            {/* Section 2: Asset Analysis (CAPM & Charts) */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Chart */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold text-white">Price Action: {ticker}</h2>
                    <div className="bg-fintech-card p-4 rounded-lg shadow-sm border border-white/10 h-[450px]">
                        {ohlcData && ohlcData.length > 0 ? (
                            <CandlestickChart data={ohlcData} height={400} />
                        ) : (
                            <div className="h-full flex items-center justify-center text-slate-400">
                                <AlertCircle className="w-5 h-5 mr-2" />
                                No Chart Data
                            </div>
                        )}
                    </div>
                </div>

                {/* Right: Risk Cards */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-white">Risk Profile</h2>

                    {/* New TimescaleDB Risk Card (Interactive) */}
                    {TICKER_MAP[ticker] && (
                        <TimeScaleRiskCard
                            assetId={TICKER_MAP[ticker]}
                            benchmarkId={BENCHMARK_ID}
                            ticker={ticker}
                        />
                    )}

                    {/* Legacy/Overview Card */}
                    {capmData ? (
                        <RiskProfileCard data={capmData} />
                    ) : (
                        <div className="h-40 bg-white/5 rounded flex items-center justify-center text-slate-400">
                            Calculating Metrics...
                        </div>
                    )}

                    <div className="bg-blue-500/10 p-4 rounded-lg text-sm text-blue-300 border border-blue-500/20">
                        <strong>Methodology Note:</strong><br />
                        • Beta: 1Y regression vs LuSE All-Share.<br />
                        • Liquidity: Penalty applied if daily vol &lt; ZMW 100k.<br />
                        • Yield Curve: Fitted to GRZ bonds (2Y-15Y).
                    </div>
                </div>
            </section>
        </div>
    );
};
