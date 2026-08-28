import clsx from 'clsx';
import { Inbox } from 'lucide-react';

function EmptyState({ icon: Icon = Inbox, title, description, action, className }) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center gap-2 rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center',
        className,
      )}
    >
      <Icon className="size-8 text-slate-400" aria-hidden="true" />
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export default EmptyState;
