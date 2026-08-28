import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

function Spinner({ label = 'Loading…', className, inline = false }) {
  return (
    <span className={clsx('inline-flex items-center gap-2 text-sm text-slate-500', className)} role="status">
      <Loader2 className="size-4 animate-spin" aria-hidden="true" />
      <span className={inline ? 'sr-only' : ''}>{label}</span>
    </span>
  );
}

export default Spinner;
