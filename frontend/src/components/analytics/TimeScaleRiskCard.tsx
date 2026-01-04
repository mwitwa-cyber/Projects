import { useState, useEffect } from 'react';
import { Loader2, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import type { RiskMetrics } from '../../types/analytics';
import { analyticsService } from '../../services/analytics';

interface TimeScaleRiskCardProps {
    assetId: number;
    benchmarkId: number;
    ticker: string;
}

const PERIODS = [
    { label: '1M', weeks: 4 },
    { label: '3M', weeks: 13 },
    { label: '6M', weeks: 26 },
    { label: '1Y', weeks: 52 },
    { label: '2Y', weeks: 104 },
];

export const TimeScaleRiskCard = ({ assetId, benchmarkId, ticker }: TimeScaleRiskCardProps) => {
    const [selectedPeriod, setSelectedPeriod] = useState(PERIODS[3]); // Default 1Y
    const [data, setData] = useState<RiskMetrics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const metrics = await analyticsService.getTimescaleRiskMetrics(
                    assetId,
                    benchmarkId,
                    selectedPeriod.weeks
                );
                setData(metrics);
            } catch (err) {
                console.error("Failed to fetch timescale risk metrics:", err);
                setError("Failed to load risk metrics");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [assetId, benchmarkId, selectedPeriod]);

    return (
        <div className="bg-fintech-card p-6 rounded-lg shadow-sm border border-white/10 relative overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Activity className="w-5 h-5 text-blue-400" />
                        Risk Analysis: {ticker}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                        Powered by TimescaleDB &bull; {selectedPeriod.weeks} weeks lookback
                    </p>
                </div>

                {/* Period Selector */}
                <div className="flex bg-white/5 rounded-lg p-1 border border-white/10">
                    {PERIODS.map((period) => (
                        <button
                            key={period.label}
                            onClick={() => setSelectedPeriod(period)}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition ${selectedPeriod.label === period.label
                                ? 'bg-blue-500 text-white shadow-sm'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {period.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="min-h-[160px]">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-fintech-card/80 backdrop-blur-sm z-10">
                        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="flex items-center justify-center h-full text-red-400 text-sm">
                        {error}
                    </div>
                ) : data ? (
                    <div className="grid grid-cols-2 gap-4">
                        {/* VaR */}
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-md">
                            <div className="text-xs text-red-300 uppercase flex items-center gap-1">
                                <TrendingDown className="w-3 h-3" /> VaR (95%)
                            </div>
                            <div className="text-2xl font-bold text-white mt-1">
                                {data.var_95.toFixed(2)}%
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                Max loss (95% conf.)
                            </div>
                        </div>

                        {/* Beta */}
                        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-md">
                            <div className="text-xs text-blue-300 uppercase flex items-center gap-1">
                                <TrendingUp className="w-3 h-3" /> Beta
                            </div>
                            <div className="text-2xl font-bold text-white mt-1">
                                {data.beta.toFixed(2)}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                vs Market (ZCCM)
                            </div>
                        </div>
                    </div>
                ) : null}

                {data && (
                    <div className="mt-4 pt-4 border-t border-white/10 text-center">
                        <p className="text-xs text-slate-500">
                            Based on {data.observation_count} weekly observations from {data.lookback_days} days history.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};
