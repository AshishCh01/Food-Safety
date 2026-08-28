import clsx from 'clsx';
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react';

const TONE_CONFIG = {
  info: { icon: Info, className: 'bg-sky-50 border-sky-200 text-sky-800' },
  success: { icon: CheckCircle2, className: 'bg-green-50 border-green-200 text-green-800' },
  warning: { icon: AlertTriangle, className: 'bg-amber-50 border-amber-200 text-amber-900' },
  danger: { icon: XCircle, className: 'bg-red-50 border-red-200 text-red-800' },
};

/** Inline banner for form/page-level messages. Danger/warning alerts use
 * role="alert" so screen readers and existing tests (`findByRole('alert')`)
 * pick them up automatically. */
function Alert({ tone = 'info', title, children, className, ...props }) {
  const { icon: Icon, className: toneClass } = TONE_CONFIG[tone] || TONE_CONFIG.info;
  const isUrgent = tone === 'danger' || tone === 'warning';
  return (
    <div
      role={isUrgent ? 'alert' : 'status'}
      className={clsx('flex gap-2 rounded-md border px-3 py-2.5 text-sm', toneClass, className)}
      {...props}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div className="min-w-0">
        {title && <p className="font-medium">{title}</p>}
        {children && <div className={clsx(title && 'mt-0.5')}>{children}</div>}
      </div>
    </div>
  );
}

export default Alert;
