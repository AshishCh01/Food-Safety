import clsx from 'clsx';
import { forwardRef } from 'react';
import { fieldClass } from './fieldStyles';

const Input = forwardRef(function Input({ className, invalid, ...props }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={clsx(fieldClass, className)}
      {...props}
    />
  );
});

export default Input;
