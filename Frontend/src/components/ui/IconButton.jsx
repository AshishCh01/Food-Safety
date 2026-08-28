import clsx from 'clsx';
import { forwardRef } from 'react';

const IconButton = forwardRef(function IconButton(
  { label, className, variant = 'ghost', size = 'md', ...props },
  ref,
) {
  const sizeClass = size === 'sm' ? 'size-8' : 'size-9';
  const variantClass =
    variant === 'ghost'
      ? 'text-slate-600 hover:bg-slate-100'
      : 'text-white bg-brand-700 hover:bg-brand-800';
  return (
    <button
      ref={ref}
      aria-label={label}
      title={label}
      className={clsx(
        'inline-flex items-center justify-center rounded-md transition-colors',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700',
        sizeClass,
        variantClass,
        className,
      )}
      {...props}
    />
  );
});

export default IconButton;
