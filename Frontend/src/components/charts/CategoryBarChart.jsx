import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../ui/EmptyState';

const BAR_COLOR = '#33587a'; // brand-600

/** Horizontal bar list for category/status breakdowns. `data` is
 * [{label, count}], sorted descending by the caller if desired. */
function CategoryBarChart({ data, height = 240 }) {
  if (!data || data.length === 0) {
    return <EmptyState title="No data yet." className="py-6" />;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="#e2e8f0" />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={140}
          tick={{ fontSize: 12, fill: '#334155' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: '#f1f5f9' }}
          contentStyle={{ fontSize: 12, borderRadius: 6, borderColor: '#e2e8f0' }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={18}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={entry.color || BAR_COLOR} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default CategoryBarChart;
