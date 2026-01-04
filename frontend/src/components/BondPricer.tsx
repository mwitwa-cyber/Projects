import { useState, useEffect, useMemo } from 'react';
import {
    TrendingUp, Loader2, AlertCircle, DollarSign, Calendar,
    Percent, ChevronDown, RotateCcw, Calculator, Clock,
    BarChart3, LineChart, Info, Zap
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    LineChart as RechartsLineChart, Line, Legend, AreaChart, Area
} from 'recharts';
import { valuationAPI } from '../services/api';
import api from '../services/api';

// GRZ (Government of Republic of Zambia) Bond Presets
const GRZ_BOND_PRESETS = [
    { name: 'GRZ 2-Year', ticker: 'GRZ-2Y', maturity: 2, coupon: 0.18, yield: 0.195, face: 100 },
    { name: 'GRZ 3-Year', ticker: 'GRZ-3Y', maturity: 3, coupon: 0.20, yield: 0.205, face: 100 },
    { name: 'GRZ 5-Year', ticker: 'GRZ-5Y', maturity: 5, coupon: 0.22, yield: 0.225, face: 100 },
    { name: 'GRZ 7-Year', ticker: 'GRZ-7Y', maturity: 7, coupon: 0.24, yield: 0.23, face: 100 },
    { name: 'GRZ 10-Year', ticker: 'GRZ-10Y', maturity: 10, coupon: 0.25, yield: 0.235, face: 100 },
    { name: 'GRZ 15-Year', ticker: 'GRZ-15Y', maturity: 15, coupon: 0.26, yield: 0.24, face: 100 },
];

interface BondResult {
    price: number;
    macaulay_duration: number;
    modified_duration: number;
}

interface CashFlow {
    period: number;
    date: string;
    coupon: number;
    principal: number;
    total: number;
    pv: number;
}

export const BondPricer = () => {
    // Form state
    const [formData, setFormData] = useState({
        face_value: 1000,
        coupon_rate: 0.22,
        yield_rate: 0.225,
        years_to_maturity: 5,
        frequency: 2,
    });

    // Results state
    const [result, setResult] = useState<BondResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // UI state
    const [activeTab, setActiveTab] = useState<'results' | 'cashflows' | 'sensitivity'>('results');
    const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
    const [showYTMCalculator, setShowYTMCalculator] = useState(false);

    // YTM Calculator state
    const [ytmInput, setYtmInput] = useState({
        price: 950,
        face_value: 1000,
        coupon_rate: 0.22,
        years_to_maturity: 5,
        frequency: 2
    });
    const [ytmResult, setYtmResult] = useState<number | null>(null);
    const [ytmLoading, setYtmLoading] = useState(false);

    // Calculate cash flows for visualization
    const cashFlows = useMemo((): CashFlow[] => {
        const flows: CashFlow[] = [];
        const periodsPerYear = formData.frequency;
        const totalPeriods = Math.ceil(formData.years_to_maturity * periodsPerYear);
        const couponPerPeriod = (formData.face_value * formData.coupon_rate) / periodsPerYear;
        const discountRate = formData.yield_rate / periodsPerYear;

        const today = new Date();

        for (let i = 1; i <= totalPeriods; i++) {
            const periodDate = new Date(today);
            periodDate.setMonth(periodDate.getMonth() + (12 / periodsPerYear) * i);

            const principal = i === totalPeriods ? formData.face_value : 0;
            const total = couponPerPeriod + principal;
            const pv = total / Math.pow(1 + discountRate, i);

            flows.push({
                period: i,
                date: periodDate.toLocaleDateString('en-ZM', { month: 'short', year: 'numeric' }),
                coupon: Math.round(couponPerPeriod * 100) / 100,
                principal,
                total: Math.round(total * 100) / 100,
                pv: Math.round(pv * 100) / 100,
            });
        }

        return flows;
    }, [formData]);

    // Calculate sensitivity data (price vs yield)
    const sensitivityData = useMemo(() => {
        const data = [];
        const baseYield = formData.yield_rate;

        for (let yieldShift = -0.05; yieldShift <= 0.05; yieldShift += 0.005) {
            const testYield = baseYield + yieldShift;
            if (testYield > 0) {
                // Simple bond price calculation
                const periodsPerYear = formData.frequency;
                const totalPeriods = Math.ceil(formData.years_to_maturity * periodsPerYear);
                const couponPerPeriod = (formData.face_value * formData.coupon_rate) / periodsPerYear;
                const discountRate = testYield / periodsPerYear;

                let price = 0;
                for (let i = 1; i <= totalPeriods; i++) {
                    const principal = i === totalPeriods ? formData.face_value : 0;
                    price += (couponPerPeriod + principal) / Math.pow(1 + discountRate, i);
                }

                data.push({
                    yield: Math.round(testYield * 1000) / 10,
                    price: Math.round(price * 100) / 100,
                    change: Math.round(((price / (result?.price || price)) - 1) * 10000) / 100,
                    isCurrent: Math.abs(yieldShift) < 0.002,
                });
            }
        }

        return data;
    }, [formData, result]);

    // Apply preset
    const applyPreset = (preset: typeof GRZ_BOND_PRESETS[0]) => {
        setFormData({
            face_value: preset.face * 10, // K1000 face value
            coupon_rate: preset.coupon,
            yield_rate: preset.yield,
            years_to_maturity: preset.maturity,
            frequency: 2, // Semi-annual for GRZ bonds
        });
        setSelectedPreset(preset.ticker);
        setResult(null);
    };

    // Handle form input changes
    const handleInputChange = (field: string, value: number) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        setSelectedPreset(null);
    };

    // Price the bond
    const handlePriceBond = async (e?: React.FormEvent) => {
        e?.preventDefault();
        setLoading(true);
        setError('');
        setResult(null);

        try {
            const data = await valuationAPI.bondPrice(formData);
            setResult(data);
            setActiveTab('results');
        } catch (err: unknown) {
            const axiosError = err as { response?: { data?: { detail?: string } } };
            setError(axiosError.response?.data?.detail || 'Failed to price bond');
        } finally {
            setLoading(false);
        }
    };

    // Calculate YTM
    const calculateYTM = async () => {
        setYtmLoading(true);
        try {
            const response = await api.post('/valuation/bond/ytm', null, {
                params: {
                    price: ytmInput.price,
                    face_value: ytmInput.face_value,
                    coupon_rate: ytmInput.coupon_rate,
                    years_to_maturity: ytmInput.years_to_maturity,
                    frequency: ytmInput.frequency,
                }
            });
            setYtmResult(response.data.yield_to_maturity);
        } catch {
            setYtmResult(null);
        } finally {
            setYtmLoading(false);
        }
    };

    // Calculate PV of all cash flows
    const totalPV = useMemo(() => cashFlows.reduce((sum, cf) => sum + cf.pv, 0), [cashFlows]);

    return (
        <div className="space-y-6">
            {/* Header with GRZ Presets */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg">
                            <DollarSign className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">Bond Pricing Calculator</h2>
                            <p className="text-slate-400 text-sm">Price bonds and analyze duration risk</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowYTMCalculator(!showYTMCalculator)}
                        className="flex items-center gap-2 px-4 py-2 text-sm border border-purple-500/50 text-purple-400 rounded-lg hover:bg-purple-500/10 transition"
                    >
                        <Calculator className="w-4 h-4" />
                        YTM Calculator
                    </button>
                </div>

                {/* GRZ Bond Presets */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-300 mb-3">
                        Quick Select: GRZ Treasury Bonds (Bank of Zambia)
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                        {GRZ_BOND_PRESETS.map(preset => (
                            <button
                                key={preset.ticker}
                                onClick={() => applyPreset(preset)}
                                className={`p-3 rounded-lg border transition text-left ${selectedPreset === preset.ticker
                                        ? 'bg-green-500/20 border-green-500/50 text-green-300'
                                        : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                                    }`}
                            >
                                <div className="font-semibold text-sm">{preset.ticker}</div>
                                <div className="text-xs text-slate-500 mt-1">
                                    {(preset.coupon * 100).toFixed(0)}% / {preset.maturity}Y
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* YTM Calculator (Collapsible) */}
                {showYTMCalculator && (
                    <div className="mb-6 bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                        <h3 className="text-purple-300 font-semibold mb-4 flex items-center gap-2">
                            <Calculator className="w-4 h-4" />
                            Yield to Maturity Calculator
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div>
                                <label className="text-xs text-slate-400">Price</label>
                                <input
                                    type="number"
                                    value={ytmInput.price}
                                    onChange={(e) => setYtmInput(p => ({ ...p, price: parseFloat(e.target.value) || 0 }))}
                                    className="w-full mt-1 bg-white/10 border border-white/20 rounded px-2 py-1.5 text-white text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-400">Face Value</label>
                                <input
                                    type="number"
                                    value={ytmInput.face_value}
                                    onChange={(e) => setYtmInput(p => ({ ...p, face_value: parseFloat(e.target.value) || 0 }))}
                                    className="w-full mt-1 bg-white/10 border border-white/20 rounded px-2 py-1.5 text-white text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-400">Coupon %</label>
                                <input
                                    type="number"
                                    value={ytmInput.coupon_rate * 100}
                                    onChange={(e) => setYtmInput(p => ({ ...p, coupon_rate: (parseFloat(e.target.value) || 0) / 100 }))}
                                    className="w-full mt-1 bg-white/10 border border-white/20 rounded px-2 py-1.5 text-white text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-400">Years</label>
                                <input
                                    type="number"
                                    value={ytmInput.years_to_maturity}
                                    onChange={(e) => setYtmInput(p => ({ ...p, years_to_maturity: parseFloat(e.target.value) || 0 }))}
                                    className="w-full mt-1 bg-white/10 border border-white/20 rounded px-2 py-1.5 text-white text-sm"
                                />
                            </div>
                            <div className="flex items-end gap-2">
                                <button
                                    onClick={calculateYTM}
                                    disabled={ytmLoading}
                                    className="flex-1 bg-purple-600 text-white py-1.5 rounded text-sm hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-1"
                                >
                                    {ytmLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                                    Calculate
                                </button>
                            </div>
                        </div>
                        {ytmResult !== null && (
                            <div className="mt-4 flex items-center gap-4">
                                <span className="text-slate-400">Yield to Maturity:</span>
                                <span className="text-2xl font-bold text-purple-400">{(ytmResult * 100).toFixed(3)}%</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Bond Parameters Form */}
                <form onSubmit={handlePriceBond} className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                <DollarSign className="w-3 h-3 inline mr-1" />
                                Face Value (K)
                            </label>
                            <input
                                type="number"
                                value={formData.face_value}
                                onChange={(e) => handleInputChange('face_value', parseFloat(e.target.value) || 0)}
                                step="100"
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-400"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                <Percent className="w-3 h-3 inline mr-1" />
                                Coupon Rate (%)
                            </label>
                            <input
                                type="number"
                                value={(formData.coupon_rate * 100).toFixed(2)}
                                onChange={(e) => handleInputChange('coupon_rate', (parseFloat(e.target.value) || 0) / 100)}
                                step="0.5"
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-400"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                <TrendingUp className="w-3 h-3 inline mr-1" />
                                Yield Rate (%)
                            </label>
                            <input
                                type="number"
                                value={(formData.yield_rate * 100).toFixed(2)}
                                onChange={(e) => handleInputChange('yield_rate', (parseFloat(e.target.value) || 0) / 100)}
                                step="0.5"
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-400"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                <Calendar className="w-3 h-3 inline mr-1" />
                                Years to Maturity
                            </label>
                            <input
                                type="number"
                                value={formData.years_to_maturity}
                                onChange={(e) => handleInputChange('years_to_maturity', parseFloat(e.target.value) || 0)}
                                step="0.5"
                                min="0.5"
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-400"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                <Clock className="w-3 h-3 inline mr-1" />
                                Frequency
                            </label>
                            <select
                                value={formData.frequency}
                                onChange={(e) => handleInputChange('frequency', parseInt(e.target.value))}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-400 [&>option]:bg-slate-800"
                            >
                                <option value={1}>Annual</option>
                                <option value={2}>Semi-annual</option>
                                <option value={4}>Quarterly</option>
                                <option value={12}>Monthly</option>
                            </select>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold py-3 rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Calculating...
                            </>
                        ) : (
                            <>
                                <DollarSign className="w-5 h-5" />
                                Calculate Bond Price
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
                    {/* Key Metrics Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-slate-400">Bond Price</span>
                                <span className={`text-xs px-2 py-0.5 rounded ${result.price > formData.face_value
                                        ? 'bg-green-500/20 text-green-400'
                                        : result.price < formData.face_value
                                            ? 'bg-red-500/20 text-red-400'
                                            : 'bg-gray-500/20 text-gray-400'
                                    }`}>
                                    {result.price > formData.face_value ? 'Premium' : result.price < formData.face_value ? 'Discount' : 'Par'}
                                </span>
                            </div>
                            <div className="text-3xl font-bold text-green-400">
                                K{result.price.toLocaleString('en-ZM', { minimumFractionDigits: 2 })}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                {((result.price / formData.face_value) * 100).toFixed(2)}% of face value
                            </div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-2">Macaulay Duration</div>
                            <div className="text-3xl font-bold text-blue-400">
                                {result.macaulay_duration.toFixed(2)}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">Years (weighted avg)</div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-2">Modified Duration</div>
                            <div className="text-3xl font-bold text-purple-400">
                                {result.modified_duration.toFixed(2)}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">Interest rate sensitivity</div>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-sm text-slate-400 mb-2">Price Change per 1% Yield Δ</div>
                            <div className="text-3xl font-bold text-orange-400">
                                ≈ {(result.modified_duration * result.price / 100).toFixed(2)}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">Kwacha (approx.)</div>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-4 border-b border-white/10">
                        <button
                            onClick={() => setActiveTab('results')}
                            className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'results'
                                    ? 'border-green-500 text-green-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            <Info className="w-4 h-4" />
                            Summary
                        </button>
                        <button
                            onClick={() => setActiveTab('cashflows')}
                            className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'cashflows'
                                    ? 'border-green-500 text-green-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            <BarChart3 className="w-4 h-4" />
                            Cash Flows
                        </button>
                        <button
                            onClick={() => setActiveTab('sensitivity')}
                            className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition ${activeTab === 'sensitivity'
                                    ? 'border-green-500 text-green-400'
                                    : 'border-transparent text-slate-400 hover:text-slate-300'
                                }`}
                        >
                            <LineChart className="w-4 h-4" />
                            Sensitivity
                        </button>
                    </div>

                    {/* Summary Tab */}
                    {activeTab === 'results' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Bond Analysis Summary</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Face Value</span>
                                        <span className="text-white font-medium">K{formData.face_value.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Coupon Rate</span>
                                        <span className="text-white font-medium">{(formData.coupon_rate * 100).toFixed(2)}% p.a.</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Annual Coupon</span>
                                        <span className="text-green-400 font-medium">K{(formData.face_value * formData.coupon_rate).toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Coupon per Period</span>
                                        <span className="text-green-400 font-medium">K{(formData.face_value * formData.coupon_rate / formData.frequency).toFixed(2)}</span>
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Yield to Maturity</span>
                                        <span className="text-white font-medium">{(formData.yield_rate * 100).toFixed(2)}% p.a.</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Years to Maturity</span>
                                        <span className="text-white font-medium">{formData.years_to_maturity} years</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Total Periods</span>
                                        <span className="text-white font-medium">{cashFlows.length} payments</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Total Cash Flows (PV)</span>
                                        <span className="text-blue-400 font-medium">K{totalPV.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Cash Flows Tab */}
                    {activeTab === 'cashflows' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Cash Flow Schedule</h3>

                            {/* Chart */}
                            <div className="h-64 mb-6">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={cashFlows}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="period" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                                        <YAxis stroke="#94a3b8" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: number, name: string) => [`K${value.toFixed(2)}`, name]}
                                        />
                                        <Legend />
                                        <Bar dataKey="coupon" name="Coupon" fill="#10b981" stackId="a" />
                                        <Bar dataKey="principal" name="Principal" fill="#3b82f6" stackId="a" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Table */}
                            <div className="max-h-64 overflow-y-auto">
                                <table className="w-full text-sm">
                                    <thead className="sticky top-0 bg-slate-800">
                                        <tr className="text-slate-400 border-b border-white/10">
                                            <th className="py-2 text-left">Period</th>
                                            <th className="py-2 text-left">Date</th>
                                            <th className="py-2 text-right">Coupon</th>
                                            <th className="py-2 text-right">Principal</th>
                                            <th className="py-2 text-right">Total</th>
                                            <th className="py-2 text-right">PV</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {cashFlows.map(cf => (
                                            <tr key={cf.period} className="border-b border-white/5 text-white">
                                                <td className="py-2">{cf.period}</td>
                                                <td className="py-2 text-slate-400">{cf.date}</td>
                                                <td className="py-2 text-right text-green-400">K{cf.coupon.toFixed(2)}</td>
                                                <td className="py-2 text-right text-blue-400">{cf.principal > 0 ? `K${cf.principal.toLocaleString()}` : '-'}</td>
                                                <td className="py-2 text-right">K{cf.total.toFixed(2)}</td>
                                                <td className="py-2 text-right text-purple-400">K{cf.pv.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot className="border-t border-white/20 font-semibold">
                                        <tr className="text-white">
                                            <td colSpan={5} className="py-2 text-right">Total Present Value:</td>
                                            <td className="py-2 text-right text-green-400">K{totalPV.toFixed(2)}</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Sensitivity Tab */}
                    {activeTab === 'sensitivity' && (
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Price-Yield Sensitivity Analysis</h3>
                            <p className="text-slate-400 text-sm mb-4">
                                Shows how bond price changes as yield moves ±5% from current level
                            </p>

                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={sensitivityData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis
                                            dataKey="yield"
                                            stroke="#94a3b8"
                                            label={{ value: 'Yield (%)', position: 'bottom', fill: '#94a3b8' }}
                                        />
                                        <YAxis
                                            stroke="#94a3b8"
                                            label={{ value: 'Price (K)', angle: -90, position: 'left', fill: '#94a3b8' }}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: number, name: string) => [
                                                name === 'price' ? `K${value.toFixed(2)}` : `${value.toFixed(2)}%`,
                                                name === 'price' ? 'Bond Price' : 'Change'
                                            ]}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="price"
                                            stroke="#10b981"
                                            fill="#10b98133"
                                            strokeWidth={2}
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="mt-4 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                <div className="flex items-start gap-2">
                                    <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                                    <div className="text-sm text-blue-200">
                                        <strong>Duration Rule of Thumb:</strong> For a {result.modified_duration.toFixed(2)} year modified duration,
                                        a 1% increase in yield will cause approximately {result.modified_duration.toFixed(2)}% decrease in price
                                        (≈K{(result.modified_duration * result.price / 100).toFixed(2)} change).
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
