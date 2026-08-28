import clsx from 'clsx';

const TONE_CLASSES = {
  neutral: 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200',
  brand: 'bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200',
  info: 'bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-200',
  success: 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-200',
  warning: 'bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-200',
  danger: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200',
  'priority-low': 'bg-priority-low/10 text-priority-low ring-1 ring-inset ring-priority-low/30',
  'priority-medium': 'bg-priority-medium/10 text-priority-medium ring-1 ring-inset ring-priority-medium/30',
  'priority-high': 'bg-priority-high/10 text-priority-high ring-1 ring-inset ring-priority-high/30',
  'priority-critical':
    'bg-priority-critical/10 text-priority-critical ring-1 ring-inset ring-priority-critical/30',
};

/** Small status/priority pill. `tone` picks the color pairing; text is always
 * shown alongside color so meaning never depends on color alone. */
function Badge({ tone = 'neutral', className, children, ...props }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap',
        TONE_CLASSES[tone] || TONE_CLASSES.neutral,
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export default Badge;
