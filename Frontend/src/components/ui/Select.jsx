import clsx from 'clsx';
import { forwardRef } from 'react';
import { fieldClass } from './fieldStyles';

const Select = forwardRef(function Select({ className, invalid, children, ...props }, ref) {
  return (
    <select
      ref={ref}
      aria-invalid={invalid || undefined}
      className={clsx(fieldClass, 'pr-8', className)}
      {...props}
    >
      {children}
    </select>
  );
});

export default Select;
