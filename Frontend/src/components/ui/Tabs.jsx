import clsx from 'clsx';

/** Controlled tab strip. Renders only the `role="tablist"` header — the
 * caller renders the matching panel based on `value` (kept intentionally
 * simple: every current use case swaps a filter/query, not full subtrees). */
function Tabs({ items, value, onChange, className }) {
  return (
    <div role="tablist" className={clsx('flex gap-1 border-b border-slate-200', className)}>
      {items.map((item) => {
        const selected = item.value === value;
        return (
          <button
            key={item.value}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(item.value)}
            className={clsx(
              '-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors',
              selected
                ? 'border-brand-700 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-700',
            )}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

export default Tabs;
