import type { CAPMResponse } from '../../types/analytics';

interface RiskProfileCardProps {
    data: CAPMResponse;
}

export const RiskProfileCard = ({ data }: RiskProfileCardProps) => {
    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Risk Profile: {data.ticker}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${data.liquidity_premium > 0.04 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                    {data.liquidity_premium > 0.04 ? 'Illiquid' : 'Liquid'}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-md">
                    <div className="text-xs text-gray-500 uppercase">Beta</div>
                    <div className="text-xl font-bold text-gray-900">{data.beta.toFixed(2)}</div>
                    <div className="text-xs text-gray-400 mt-1">Market Sensitivity</div>
                </div>

                <div className="p-3 bg-gray-50 rounded-md">
                    <div className="text-xs text-gray-500 uppercase">Exp. Return</div>
                    <div className="text-xl font-bold text-indigo-600">{(data.expected_return * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-400 mt-1">Annualized CAPM</div>
                </div>

                <div className="p-3 bg-gray-50 rounded-md">
                    <div className="text-xs text-gray-500 uppercase">Liquidity Prem.</div>
                    <div className="text-xl font-bold text-orange-600">{(data.liquidity_premium * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-400 mt-1">Volume Penalty</div>
                </div>

                <div className="p-3 bg-gray-50 rounded-md">
                    <div className="text-xs text-gray-500 uppercase">Mkt Return</div>
                    <div className="text-xl font-bold text-gray-900">{(data.annualized_market_return * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-400 mt-1">Benchmark</div>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-400">
                Avg. Daily Dollar Vol: ZMW {data.average_dollar_volume.toLocaleString()}
            </div>
        </div>
    );
};
