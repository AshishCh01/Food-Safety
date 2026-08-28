import { formatStatusLabel } from '../../utils/complaintStatus';
import { formatDateTime } from '../../utils/formatters';
import EmptyState from '../ui/EmptyState';

function ComplaintTimeline({ entries }) {
  if (!entries || entries.length === 0) {
    return <EmptyState title="No status changes recorded yet." />;
  }

  return (
    <ol className="flex flex-col gap-4">
      {entries.map((entry) => (
        <li key={entry.id} className="relative border-l-2 border-brand-200 pl-4">
          <span className="absolute -left-1.25 top-1 size-2 rounded-full bg-brand-600" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-900">
            {entry.old_status ? (
              <>
                {formatStatusLabel(entry.old_status)} &rarr; {formatStatusLabel(entry.new_status)}
              </>
            ) : (
              formatStatusLabel(entry.new_status)
            )}
          </p>
          <p className="text-xs text-slate-500">
            {entry.changed_by_name} &middot; {formatDateTime(entry.created_at)}
          </p>
          {entry.reason && <p className="mt-1 text-sm text-slate-600">{entry.reason}</p>}
        </li>
      ))}
    </ol>
  );
}

export default ComplaintTimeline;
