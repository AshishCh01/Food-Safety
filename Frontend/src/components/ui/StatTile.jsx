import clsx from 'clsx';
import Card from './Card';

/** Compact KPI tile used across every dashboard. `tone` tints the icon only
 * (keeps a grid of tiles from turning into a wall of color). */
const ICON_TONE = {
  neutral: 'bg-slate-100 text-slate-600',
  brand: 'bg-brand-50 text-brand-700',
  success: 'bg-green-50 text-green-700',
  warning: 'bg-amber-50 text-amber-700',
  danger: 'bg-red-50 text-red-700',
};

function StatTile({ label, value, icon: Icon, tone = 'neutral', hint, className }) {
  return (
    <Card className={clsx('flex items-start gap-3', className)}>
      {Icon && (
        <span className={clsx('flex size-9 shrink-0 items-center justify-center rounded-md', ICON_TONE[tone])}>
          <Icon className="size-4.5" aria-hidden="true" />
        </span>
      )}
      <div className="min-w-0">
        <p className="text-xs font-medium text-slate-500">{label}</p>
        <p className="text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
        {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
      </div>
    </Card>
  );
}

export default StatTile;
