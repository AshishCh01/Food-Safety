import clsx from 'clsx';
import { forwardRef } from 'react';
import { fieldClass } from './fieldStyles';

const Textarea = forwardRef(function Textarea({ className, invalid, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={clsx(fieldClass, 'min-h-24 resize-y', className)}
      {...props}
    />
  );
});

export default Textarea;
