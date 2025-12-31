import { useState, useEffect } from 'react';
import { YieldCurveChart } from '../components/charts/YieldCurveChart';
import { CandlestickChart } from '../components/charts/CandlestickChart';
import { RiskProfileCard } from '../components/analytics/RiskProfileCard';
import { analyticsService } from '../services/analytics';
import type { YieldCurveResponse, OHLCData, CAPMResponse } from '../types/analytics';
import { AlertCircle } from 'lucide-react';

export const AnalyticsDashboard = () => {
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

    if (loading && !yieldData) return <div className="p-8 text-center">Loading Analytics...</div>;
    if (error) return <div className="p-8 text-center text-red-600">Error: {error}</div>;

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Advanced Analytics</h1>
                    <p className="text-gray-500">Quantitative modeling and risk assessment</p>
                </div>

                {/* Simple Ticker Selector */}
                <select
                    value={ticker}
                    onChange={handleTickerChange}
                    className="p-2 border rounded-md shadow-sm bg-white"
                >
                    <option value="ZNCO">ZNCO (Liquid)</option>
                    <option value="MAFS">MAFS (Illiquid)</option>
                    <option value="AECI">AECI</option>
                    <option value="CECZ">CECZ</option>
                    <option value="GRZ-10Y">GRZ-10Y (Bond)</option>
                </select>
            </div>

            {/* Section 1: Macro (Yield Curve) */}
            <section>
                <div className="mb-4 flex items-center gap-2">
                    <h2 className="text-xl font-semibold text-gray-800">Macro: Yield Curve</h2>
                    {yieldData?.parameters && <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Nelson-Siegel Fit</span>}
                </div>
                {yieldData ? (
                    <YieldCurveChart
                        curveData={yieldData.curve}
                        observedData={yieldData.observed}
                        parameters={yieldData.parameters}
                    />
                ) : (
                    <div className="h-64 bg-gray-50 rounded flex items-center justify-center text-gray-400">
                        Yield Curve Data Unavailable
                    </div>
                )}
            </section>

            {/* Section 2: Asset Analysis (CAPM & Charts) */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Chart */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold text-gray-800">Price Action: {ticker}</h2>
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 h-[450px]">
                        {ohlcData && ohlcData.length > 0 ? (
                            <CandlestickChart data={ohlcData} height={400} />
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-400">
                                <AlertCircle className="w-5 h-5 mr-2" />
                                No Chart Data
                            </div>
                        )}
                    </div>
                </div>

                {/* Right: Risk Card */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-gray-800">Risk Profile</h2>
                    {capmData ? (
                        <RiskProfileCard data={capmData} />
                    ) : (
                        <div className="h-40 bg-gray-50 rounded flex items-center justify-center text-gray-400">
                            Calculating Metrics...
                        </div>
                    )}

                    <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-800 border border-blue-100">
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
