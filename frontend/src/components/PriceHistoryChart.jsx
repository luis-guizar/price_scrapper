import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

/**
 * Shared price-history line chart. `data` is an array of { date, price } points.
 * Optionally pass `minPrice` / `maxPrice` to draw dashed reference lines for the
 * product's historical low / high (used by the Sephora deals view).
 */
export default function PriceHistoryChart({ data, minPrice = null, maxPrice = null }) {
    return (
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickCount={5} />
                <YAxis stroke="#94a3b8" fontSize={12} domain={['auto', 'auto']} tickFormatter={(val) => `$${val}`} />
                <Tooltip
                    contentStyle={{ backgroundColor: 'rgba(15,23,42,0.95)', borderColor: 'rgba(100,116,139,0.3)', borderRadius: '12px', boxShadow: '0 20px 40px -8px rgba(0,0,0,0.7)', color: '#f1f5f9', fontSize: '13px', padding: '10px 14px' }}
                    itemStyle={{ color: '#93c5fd', fontWeight: '600' }}
                    labelStyle={{ color: '#94a3b8', fontSize: '11px', marginBottom: '4px' }}
                />
                {maxPrice != null && (
                    <ReferenceLine y={maxPrice} stroke="#64748b" strokeDasharray="4 4"
                        label={{ value: `High $${maxPrice.toLocaleString()}`, position: 'insideTopRight', fill: '#94a3b8', fontSize: 10 }} />
                )}
                {minPrice != null && (
                    <ReferenceLine y={minPrice} stroke="#fb7185" strokeDasharray="4 4"
                        label={{ value: `Low $${minPrice.toLocaleString()}`, position: 'insideBottomRight', fill: '#fb7185', fontSize: 10 }} />
                )}
                <Line type="monotone" dataKey="price" stroke="#60a5fa" strokeWidth={2.5} dot={{ r: 3.5, fill: '#60a5fa', strokeWidth: 0 }} activeDot={{ r: 5.5, fill: '#93c5fd', strokeWidth: 0 }} />
            </LineChart>
        </ResponsiveContainer>
    )
}
