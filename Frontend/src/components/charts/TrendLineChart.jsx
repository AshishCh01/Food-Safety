import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../ui/EmptyState';
import { formatDate } from '../../utils/formatters';

/** Simple trend line for `[{date, count}]` time series (complaint_trend). */
function TrendLineChart({ data, height = 200 }) {
  if (!data || data.length === 0) {
    return <EmptyState title="No trend data yet." className="py-6" />;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ left: -16, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="#e2e8f0" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => formatDate(value)}
          tick={{ fontSize: 11, fill: '#64748b' }}
          axisLine={false}
          tickLine={false}
          minTickGap={24}
        />
        <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
        <Tooltip
          labelFormatter={(value) => formatDate(value)}
          contentStyle={{ fontSize: 12, borderRadius: 6, borderColor: '#e2e8f0' }}
        />
        <Line type="monotone" dataKey="count" stroke="#33587a" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default TrendLineChart;
