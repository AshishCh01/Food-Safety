import clsx from 'clsx';
import { forwardRef } from 'react';

const Checkbox = forwardRef(function Checkbox({ className, label, id, ...props }, ref) {
  return (
    <label htmlFor={id} className="inline-flex items-center gap-2 text-sm text-slate-700">
      <input
        ref={ref}
        id={id}
        type="checkbox"
        className={clsx(
          'size-4 rounded border-slate-300 text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-brand-700',
          className,
        )}
        {...props}
      />
      {label}
    </label>
  );
});

export default Checkbox;
