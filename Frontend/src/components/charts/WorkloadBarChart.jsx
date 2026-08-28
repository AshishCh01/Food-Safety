import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../ui/EmptyState';

// info/warning/success tones, matching Badge's assignment-status colors
const SERIES = [
  { key: 'assigned_count', name: 'Assigned', color: '#0284c7' },
  { key: 'in_progress_count', name: 'In progress', color: '#d97706' },
  { key: 'completed_count', name: 'Completed', color: '#16a34a' },
];

/** Stacked bar chart of inspector workload: `data` is the
 * `inspector_workload` array from DistrictAnalytics. */
function WorkloadBarChart({ data, height = 240 }) {
  if (!data || data.length === 0) {
    return <EmptyState title="No inspectors in this district yet." className="py-6" />;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ left: -16, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="#e2e8f0" />
        <XAxis
          dataKey="inspector_name"
          tick={{ fontSize: 11, fill: '#64748b' }}
          axisLine={false}
          tickLine={false}
          interval={0}
          angle={-20}
          textAnchor="end"
          height={50}
        />
        <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6, borderColor: '#e2e8f0' }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {SERIES.map((series) => (
          <Bar key={series.key} dataKey={series.key} name={series.name} stackId="workload" fill={series.color} maxBarSize={28} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export default WorkloadBarChart;
