import type { CAPMResponse } from '../../types/analytics';

interface RiskProfileCardProps {
    data: CAPMResponse;
}

export const RiskProfileCard = ({ data }: RiskProfileCardProps) => {
    return (
        <div className="bg-fintech-card p-6 rounded-lg shadow-sm border border-white/10">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white">Risk Profile: {data.ticker}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${data.liquidity_premium > 0.04 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                    {data.liquidity_premium > 0.04 ? 'Illiquid' : 'Liquid'}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-white/5 rounded-md">
                    <div className="text-xs text-slate-400 uppercase">Beta</div>
                    <div className="text-xl font-bold text-white">{data.beta.toFixed(2)}</div>
                    <div className="text-xs text-slate-500 mt-1">Market Sensitivity</div>
                </div>

                <div className="p-3 bg-white/5 rounded-md">
                    <div className="text-xs text-slate-400 uppercase">Exp. Return</div>
                    <div className="text-xl font-bold text-indigo-400">{(data.expected_return * 100).toFixed(1)}%</div>
                    <div className="text-xs text-slate-500 mt-1">Annualized CAPM</div>
                </div>

                <div className="p-3 bg-white/5 rounded-md">
                    <div className="text-xs text-slate-400 uppercase">Liquidity Prem.</div>
                    <div className="text-xl font-bold text-orange-400">{(data.liquidity_premium * 100).toFixed(1)}%</div>
                    <div className="text-xs text-slate-500 mt-1">Volume Penalty</div>
                </div>

                <div className="p-3 bg-white/5 rounded-md">
                    <div className="text-xs text-slate-400 uppercase">Mkt Return</div>
                    <div className="text-xl font-bold text-white">{(data.annualized_market_return * 100).toFixed(1)}%</div>
                    <div className="text-xs text-slate-500 mt-1">Benchmark</div>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t border-white/10 text-xs text-slate-400">
                Avg. Daily Dollar Vol: ZMW {data.average_dollar_volume.toLocaleString()}
            </div>
        </div>
    );
};
