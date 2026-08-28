import clsx from 'clsx';

/** `<dt>`/`<dd>` pairs laid out as a label/value grid. Children are the raw
 * dt/dd elements (unchanged from before), only the wrapper is new. */
function DetailGrid({ children, className }) {
  return (
    <dl
      className={clsx(
        'grid grid-cols-1 gap-x-4 gap-y-1.5 text-sm sm:grid-cols-[max-content_1fr] sm:items-baseline',
        '[&>dt]:font-medium [&>dt]:text-slate-500 [&>dd]:m-0 [&>dd]:text-slate-800',
        className,
      )}
    >
      {children}
    </dl>
  );
}

export default DetailGrid;
