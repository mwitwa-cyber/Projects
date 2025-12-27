import { useState } from 'react';
<<<<<<< Updated upstream
import type { FormEvent } from 'react';
=======
>>>>>>> Stashed changes
import { Loader2, AlertCircle, TrendingDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { riskAPI, optimizationAPI } from '../services/api';

<<<<<<< Updated upstream
// Types for API results
=======
>>>>>>> Stashed changes
interface RiskResult {
    var_value: number;
    confidence_level: number;
    method: string;
}

interface CVaRResult {
    cvar_value: number;
    confidence_level: number;
}

interface BetaResult {
    beta: number;
    alpha?: number;
    r_squared?: number;
}

<<<<<<< Updated upstream
/**
 * RiskAnalyzer component: UI for Value at Risk (VaR), CVaR, and Beta analytics.
 */
=======
>>>>>>> Stashed changes
export const RiskAnalyzer = () => {
    const [activeTab, setActiveTab] = useState<'var' | 'beta'>('var');

    // VaR State
<<<<<<< Updated upstream
    const [varReturns, setVarReturns] = useState<string>('0.02, -0.03, 0.04, -0.01, 0.05, 0.03, -0.02, 0.01, 0.06, -0.04');
    const [varConfidence, setVarConfidence] = useState<number>(0.95);
    const [varMethod, setVarMethod] = useState<'historical' | 'parametric' | 'monte_carlo'>('historical');
    const [varResult, setVarResult] = useState<RiskResult | null>(null);
    const [cvarResult, setCvarResult] = useState<CVaRResult | null>(null);
    const [varLoading, setVarLoading] = useState<boolean>(false);
    const [varError, setVarError] = useState<string>('');

    // Beta State
    const [assetReturns, setAssetReturns] = useState<string>('0.02, 0.03, -0.01, 0.04, 0.01, 0.02, -0.02, 0.03');
    const [marketReturns, setMarketReturns] = useState<string>('0.01, 0.02, -0.005, 0.03, 0.015, 0.01, -0.01, 0.025');
    const [betaResult, setBetaResult] = useState<BetaResult | null>(null);
    const [betaLoading, setBetaLoading] = useState<boolean>(false);
    const [betaError, setBetaError] = useState<string>('');

    // VaR Handler
    const handleCalculateVaR = async (e: FormEvent) => {
=======
    const [varReturns, setVarReturns] = useState('0.02, -0.03, 0.04, -0.01, 0.05, 0.03, -0.02, 0.01, 0.06, -0.04');
    const [varConfidence, setVarConfidence] = useState(0.95);
    const [varMethod, setVarMethod] = useState<'historical' | 'parametric' | 'monte_carlo'>('historical');
    const [varResult, setVarResult] = useState<RiskResult | null>(null);
    const [cvarResult, setCvarResult] = useState<CVaRResult | null>(null);
    const [varLoading, setVarLoading] = useState(false);
    const [varError, setVarError] = useState('');

    // Beta State
    const [assetReturns, setAssetReturns] = useState('0.02, 0.03, -0.01, 0.04, 0.01, 0.02, -0.02, 0.03');
    const [marketReturns, setMarketReturns] = useState('0.01, 0.02, -0.005, 0.03, 0.015, 0.01, -0.01, 0.025');
    const [betaResult, setBetaResult] = useState<BetaResult | null>(null);
    const [betaLoading, setBetaLoading] = useState(false);
    const [betaError, setBetaError] = useState('');

    // VaR Handler
    const handleCalculateVaR = async (e: React.FormEvent) => {
>>>>>>> Stashed changes
        e.preventDefault();
        setVarLoading(true);
        setVarError('');
        setVarResult(null);
        setCvarResult(null);

        try {
            const returns = varReturns
                .split(',')
<<<<<<< Updated upstream
                .map((v: string) => parseFloat(v.trim()))
                .filter((v: number) => !isNaN(v));
=======
                .map(v => parseFloat(v.trim()))
                .filter(v => !isNaN(v));
>>>>>>> Stashed changes

            if (returns.length === 0) {
                setVarError('Please enter valid return values');
                setVarLoading(false);
                return;
            }

            // Calculate VaR
            const varData = await riskAPI.valueAtRisk({
                returns,
                confidence_level: varConfidence,
                method: varMethod,
            });

            setVarResult(varData);

            // Calculate CVaR if confidence level is suitable
            if (varConfidence >= 0.90) {
                const cvarData = await riskAPI.conditionalVaR({
                    returns,
                    confidence_level: varConfidence,
                    method: varMethod === 'monte_carlo' ? 'historical' : varMethod,
                });

                setCvarResult(cvarData);
            }
        } catch (err: any) {
            setVarError(err.response?.data?.detail || 'VaR calculation failed');
        } finally {
            setVarLoading(false);
        }
    };

    // Beta Handler
    const handleCalculateBeta = async (e: React.FormEvent) => {
        e.preventDefault();
        setBetaLoading(true);
        setBetaError('');
        setBetaResult(null);

        try {
            const asset = assetReturns
                .split(',')
                .map(v => parseFloat(v.trim()))
                .filter(v => !isNaN(v));

            const market = marketReturns
                .split(',')
                .map(v => parseFloat(v.trim()))
                .filter(v => !isNaN(v));

            if (asset.length === 0 || market.length === 0) {
                setBetaError('Please enter valid return values for both asset and market');
                setBetaLoading(false);
                return;
            }

            if (asset.length !== market.length) {
                setBetaError('Asset and market returns must have the same number of periods');
                setBetaLoading(false);
                return;
            }

            const data = await optimizationAPI.calculateBeta({
                asset_returns: asset,
                market_returns: market,
            });

            setBetaResult(data);
        } catch (err: any) {
            setBetaError(err.response?.data?.detail || 'Beta calculation failed');
        } finally {
            setBetaLoading(false);
        }
    };

    const getChartData = () => {
        try {
            const returns = varReturns
                .split(',')
                .map(v => parseFloat(v.trim()))
                .filter(v => !isNaN(v));

            return returns.map((value, index) => ({
                period: index + 1,
                return: Number((value * 100).toFixed(2)),
            }));
        } catch {
            return [];
        }
    };

    const getBetaChartData = () => {
        try {
            const asset = assetReturns
                .split(',')
                .map(v => parseFloat(v.trim()))
                .filter(v => !isNaN(v));

            const market = marketReturns
                .split(',')
                .map(v => parseFloat(v.trim()))
                .filter(v => !isNaN(v));

            return asset.map((value, index) => ({
                period: index + 1,
                asset: Number((value * 100).toFixed(2)),
                market: Number((market[index] * 100).toFixed(2)),
            }));
        } catch {
            return [];
        }
    };

    return (
        <div className="space-y-6">
            {/* Tabs */}
            <div className="flex gap-4 border-b border-white/10">
                <button
                    onClick={() => setActiveTab('var')}
                    className={`px-4 py-2 font-medium border-b-2 transition ${activeTab === 'var'
<<<<<<< Updated upstream
                        ? 'border-red-500 text-red-400'
                        : 'border-transparent text-slate-400 hover:text-slate-300'
=======
                            ? 'border-red-500 text-red-400'
                            : 'border-transparent text-slate-400 hover:text-slate-300'
>>>>>>> Stashed changes
                        }`}
                >
                    Value at Risk
                </button>
                <button
                    onClick={() => setActiveTab('beta')}
                    className={`px-4 py-2 font-medium border-b-2 transition ${activeTab === 'beta'
<<<<<<< Updated upstream
                        ? 'border-blue-500 text-blue-400'
                        : 'border-transparent text-slate-400 hover:text-slate-300'
=======
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-slate-400 hover:text-slate-300'
>>>>>>> Stashed changes
                        }`}
                >
                    Beta Calculation
                </button>
            </div>

            {/* VaR Tab */}
            {activeTab === 'var' && (
                <div className="space-y-6">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-6">
                            <TrendingDown className="w-6 h-6 text-red-400" />
                            <h2 className="text-2xl font-bold text-white">Value at Risk (VaR) Analysis</h2>
                        </div>

                        <form onSubmit={handleCalculateVaR} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Return Series (comma-separated)
                                </label>
                                <textarea
                                    value={varReturns}
                                    onChange={(e) => setVarReturns(e.target.value)}
                                    placeholder="0.02, -0.03, 0.04, -0.01, 0.05"
                                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                                    rows={3}
                                />
                                <p className="text-xs text-slate-400 mt-1">Enter daily/weekly/monthly returns as decimals</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Confidence Level
                                    </label>
                                    <div className="flex gap-2">
                                        {[0.90, 0.95, 0.99].map(level => (
                                            <button
                                                key={level}
                                                type="button"
                                                onClick={() => setVarConfidence(level)}
                                                className={`flex-1 py-2 px-3 rounded-lg font-medium transition ${varConfidence === level
<<<<<<< Updated upstream
                                                    ? 'bg-red-500/30 border border-red-500 text-red-300'
                                                    : 'bg-white/10 border border-white/20 text-slate-300 hover:bg-white/15'
=======
                                                        ? 'bg-red-500/30 border border-red-500 text-red-300'
                                                        : 'bg-white/10 border border-white/20 text-slate-300 hover:bg-white/15'
>>>>>>> Stashed changes
                                                    }`}
                                            >
                                                {(level * 100).toFixed(0)}%
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Calculation Method
                                    </label>
                                    <select
                                        value={varMethod}
                                        onChange={(e) => setVarMethod(e.target.value as any)}
                                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-400"
                                    >
                                        <option value="historical">Historical Simulation</option>
                                        <option value="parametric">Parametric (Normal)</option>
                                        <option value="monte_carlo">Monte Carlo</option>
                                    </select>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={varLoading}
                                className="w-full bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold py-3 rounded-lg hover:from-red-600 hover:to-red-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
                            >
                                {varLoading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Calculating...
                                    </>
                                ) : (
                                    'Calculate VaR'
                                )}
                            </button>
                        </form>

                        {varError && (
                            <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex gap-3">
                                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                                <div className="text-red-200 text-sm">{varError}</div>
                            </div>
                        )}

                        {/* Chart */}
                        {getChartData().length > 0 && (
                            <div className="mt-8 bg-white/5 rounded-xl p-6 border border-white/10">
                                <h3 className="text-lg font-semibold text-white mb-4">Return Distribution</h3>
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={getChartData()}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="period" stroke="#94a3b8" />
                                            <YAxis stroke="#94a3b8" />
                                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                                            <Bar
                                                dataKey="return"
                                                fill="#3b82f6"
                                                radius={[4, 4, 0, 0]}
                                            />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Results */}
                    {(varResult || cvarResult) && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {varResult && (
                                <div className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-xl p-6">
                                    <div className="text-sm text-slate-400 mb-2">Value at Risk ({(varResult.confidence_level * 100).toFixed(0)}%)</div>
                                    <div className="text-3xl font-bold text-red-400">
                                        {(varResult.var_value * 100).toFixed(2)}%
                                    </div>
                                    <div className="text-xs text-slate-500 mt-2">Max expected loss ({varResult.method})</div>
                                </div>
                            )}

                            {cvarResult && (
                                <div className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-xl p-6">
                                    <div className="text-sm text-slate-400 mb-2">Conditional VaR (Expected Shortfall)</div>
                                    <div className="text-3xl font-bold text-orange-400">
                                        {(cvarResult.cvar_value * 100).toFixed(2)}%
                                    </div>
                                    <div className="text-xs text-slate-500 mt-2">Average loss beyond VaR</div>
                                </div>
                            )}

                            {varResult && cvarResult && (
                                <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-6">
                                    <div className="text-sm text-slate-400 mb-2">Risk Interpretation</div>
                                    <div className="text-sm text-blue-300 space-y-2">
                                        <p>There's a {(varResult.confidence_level * 100).toFixed(0)}% chance returns will not fall below {(varResult.var_value * 100).toFixed(2)}%</p>
                                        <p>If losses exceed VaR, average loss is {(cvarResult.cvar_value * 100).toFixed(2)}%</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Beta Tab */}
            {activeTab === 'beta' && (
                <div className="space-y-6">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
                        <h2 className="text-2xl font-bold text-white mb-6">Systematic Risk (Beta) Calculation</h2>

                        <form onSubmit={handleCalculateBeta} className="space-y-6">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Asset Returns (comma-separated)
                                    </label>
                                    <textarea
                                        value={assetReturns}
                                        onChange={(e) => setAssetReturns(e.target.value)}
                                        placeholder="0.02, 0.03, -0.01, 0.04"
                                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                                        rows={4}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Market Returns (comma-separated)
                                    </label>
                                    <textarea
                                        value={marketReturns}
                                        onChange={(e) => setMarketReturns(e.target.value)}
                                        placeholder="0.01, 0.02, -0.005, 0.03"
                                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                                        rows={4}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={betaLoading}
                                className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold py-3 rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
                            >
                                {betaLoading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Calculating...
                                    </>
                                ) : (
                                    'Calculate Beta'
                                )}
                            </button>
                        </form>

                        {betaError && (
                            <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex gap-3">
                                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                                <div className="text-red-200 text-sm">{betaError}</div>
                            </div>
                        )}

                        {/* Chart */}
                        {getBetaChartData().length > 0 && (
                            <div className="mt-8 bg-white/5 rounded-xl p-6 border border-white/10">
                                <h3 className="text-lg font-semibold text-white mb-4">Returns Comparison</h3>
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={getBetaChartData()}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="period" stroke="#94a3b8" />
                                            <YAxis stroke="#94a3b8" />
                                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                                            <Legend />
                                            <Line type="monotone" dataKey="asset" stroke="#3b82f6" strokeWidth={2} name="Asset" />
                                            <Line type="monotone" dataKey="market" stroke="#10b981" strokeWidth={2} name="Market" />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Results */}
                    {betaResult && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-6">
                                <div className="text-sm text-slate-400 mb-2">Beta (β)</div>
                                <div className="text-3xl font-bold text-blue-400">{betaResult.beta.toFixed(3)}</div>
                                <div className="text-xs text-slate-500 mt-2">
                                    {betaResult.beta > 1 ? 'More volatile than market' : betaResult.beta < 1 ? 'Less volatile than market' : 'Moves with market'}
                                </div>
                            </div>

                            {betaResult.alpha !== undefined && (
                                <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-6">
                                    <div className="text-sm text-slate-400 mb-2">Alpha (α)</div>
                                    <div className="text-3xl font-bold text-green-400">
                                        {(betaResult.alpha * 100).toFixed(2)}%
                                    </div>
                                    <div className="text-xs text-slate-500 mt-2">Excess return (risk-adjusted)</div>
                                </div>
                            )}

                            {betaResult.r_squared !== undefined && (
                                <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-6">
                                    <div className="text-sm text-slate-400 mb-2">R² (Model Fit)</div>
                                    <div className="text-3xl font-bold text-purple-400">{(betaResult.r_squared * 100).toFixed(1)}%</div>
                                    <div className="text-xs text-slate-500 mt-2">% variation explained by market</div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
