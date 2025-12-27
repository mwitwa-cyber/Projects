import { useState } from 'react';
import { TrendingUp, Loader2, AlertCircle } from 'lucide-react';
import { valuationAPI } from '../services/api';

interface BondResult {
    price: number;
    macaulay_duration?: number;
    modified_duration?: number;
}

export const BondPricer = () => {
    const [formData, setFormData] = useState({
        face_value: 100,
        coupon_rate: 0.10,
        yield_rate: 0.12,
        years_to_maturity: 5,
        frequency: 2,
    });

    const [result, setResult] = useState<BondResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: parseFloat(value) || 0,
        }));
    };

    const handlePriceBond = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setResult(null);

        try {
            const data = await valuationAPI.bondPrice(formData);
            setResult(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to price bond');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-6">
                <TrendingUp className="w-6 h-6 text-blue-400" />
                <h2 className="text-2xl font-bold text-white">Bond Pricing Calculator</h2>
            </div>

            <form onSubmit={handlePriceBond} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Face Value (K)
                        </label>
                        <input
                            type="number"
                            name="face_value"
                            value={formData.face_value}
                            onChange={handleInputChange}
                            step="0.01"
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Coupon Rate (% p.a.)
                        </label>
                        <input
                            type="number"
                            name="coupon_rate"
                            value={formData.coupon_rate * 100}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                coupon_rate: parseFloat(e.target.value) / 100 || 0,
                            }))}
                            step="0.01"
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Yield Rate (% p.a.)
                        </label>
                        <input
                            type="number"
                            name="yield_rate"
                            value={formData.yield_rate * 100}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                yield_rate: parseFloat(e.target.value) / 100 || 0,
                            }))}
                            step="0.01"
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Years to Maturity
                        </label>
                        <input
                            type="number"
                            name="years_to_maturity"
                            value={formData.years_to_maturity}
                            onChange={handleInputChange}
                            step="0.5"
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Payment Frequency (times/year)
                        </label>
                        <select
                            name="frequency"
                            value={formData.frequency}
                            onChange={(e) => setFormData(prev => ({
                                ...prev,
                                frequency: parseInt(e.target.value),
                            }))}
                            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-400"
                        >
                            <option value={1}>Annual (1)</option>
                            <option value={2}>Semi-annual (2)</option>
                            <option value={4}>Quarterly (4)</option>
                            <option value={12}>Monthly (12)</option>
                        </select>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold py-3 rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Calculating...
                        </>
                    ) : (
                        'Calculate Bond Price'
                    )}
                </button>
            </form>

            {error && (
                <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="text-red-200 text-sm">{error}</div>
                </div>
            )}

            {result && (
                <div className="mt-8 bg-gradient-to-br from-green-500/10 to-blue-500/10 border border-green-500/30 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-6">Pricing Results</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white/5 rounded-lg p-4">
                            <div className="text-sm text-slate-400 mb-1">Bond Price</div>
                            <div className="text-3xl font-bold text-green-400">
                                K{result.price.toFixed(2)}
                            </div>
                            <div className="text-xs text-slate-500 mt-2">
                                {result.price > formData.face_value ? 'Premium' : 'Discount'} Bond
                            </div>
                        </div>

                        {result.macaulay_duration && (
                            <div className="bg-white/5 rounded-lg p-4">
                                <div className="text-sm text-slate-400 mb-1">Macaulay Duration</div>
                                <div className="text-3xl font-bold text-blue-400">
                                    {result.macaulay_duration.toFixed(2)} yrs
                                </div>
                                <div className="text-xs text-slate-500 mt-2">Weighted avg time to cash flows</div>
                            </div>
                        )}

                        {result.modified_duration && (
                            <div className="bg-white/5 rounded-lg p-4">
                                <div className="text-sm text-slate-400 mb-1">Modified Duration</div>
                                <div className="text-3xl font-bold text-purple-400">
                                    {result.modified_duration.toFixed(2)} yrs
                                </div>
                                <div className="text-xs text-slate-500 mt-2">Interest rate sensitivity</div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
