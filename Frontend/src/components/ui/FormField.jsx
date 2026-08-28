import clsx from 'clsx';

/** Label + hint/error wrapper. Pass `htmlFor` matching the child field's `id`
 * so labels stay associated for screen readers and existing `getByLabelText`
 * tests. */
function FormField({ label, htmlFor, hint, error, required, className, children }) {
  return (
    <div className={clsx('flex flex-col gap-1.5', className)}>
      {label && (
        <label htmlFor={htmlFor} className="text-sm font-medium text-slate-700">
          {label}
          {required && <span className="text-red-600"> *</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && (
        <p role="alert" className="text-xs font-medium text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

export default FormField;
