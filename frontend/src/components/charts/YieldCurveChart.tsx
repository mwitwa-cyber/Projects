import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { YieldCurvePoint, YieldCurveParams } from '../../types/analytics';

interface YieldCurveChartProps {
    curveData: YieldCurvePoint[];
    observedData?: YieldCurvePoint[];
    parameters?: YieldCurveParams;
}

export const YieldCurveChart = ({ curveData, parameters }: YieldCurveChartProps) => {
    // Combine data for display if needed, but Recharts handles independent series best via multiple components or composited data.
    // For curve + scatter overlay, we can use ComposedChart, but let's stick to LineChart for the curve and standard Dots for observed.
    // Actually, Recharts ComposedChart is best for Line + Scatter.

    // Let's create a ComposedChart
    // We need to merge observed data or overlay it.
    // Simpler: Just plotting the curve first.

    return (
        <div className="w-full h-[400px] bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Nelson-Siegel Yield Curve</h3>
            {parameters && (
                <div className="flex gap-4 mb-4 text-xs text-gray-500">
                    <span>Beta0: {parameters.beta0}</span>
                    <span>Beta1: {parameters.beta1}</span>
                    <span>Beta2: {parameters.beta2}</span>
                    <span>Lambda: {parameters.lambda}</span>
                </div>
            )}

            <ResponsiveContainer width="100%" height="100%">
                <LineChart
                    data={curveData}
                    margin={{
                        top: 5,
                        right: 30,
                        left: 20,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                        dataKey="ttm"
                        label={{ value: 'Maturity (Years)', position: 'insideBottomRight', offset: -10 }}
                        type="number"
                        domain={[0, 'dataMax']}
                        tickCount={10}
                    />
                    <YAxis
                        label={{ value: 'Yield (%)', angle: -90, position: 'insideLeft' }}
                        domain={['auto', 'auto']}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee' }}
                        formatter={(value: any) => [`${Number(value).toFixed(2)}%`, 'Yield']}
                        labelFormatter={(label) => `${label} Years`}
                    />
                    <Legend />
                    <Line
                        type="monotone"
                        dataKey="yield"
                        stroke="#8884d8"
                        strokeWidth={3}
                        dot={false}
                        name="Fitted Curve"
                        activeDot={{ r: 8 }}
                    />
                    {/* Overlay Observed Data if Recharts allows easily multiple sources? 
                         It usually requires unified data. 
                         Let's skip observed points for now to keep it simple, or add them as ReferenceDots if few.
                     */}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
