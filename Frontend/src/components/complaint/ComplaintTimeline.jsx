import { formatStatusLabel } from '../../utils/complaintStatus';

function ComplaintTimeline({ entries }) {
  if (!entries || entries.length === 0) {
    return <p>No status changes recorded yet.</p>;
  }

  return (
    <ol className="timeline">
      {entries.map((entry) => (
        <li key={entry.id} className="timeline-entry">
          <div className="timeline-entry-title">
            {entry.old_status ? (
              <>
                {formatStatusLabel(entry.old_status)} &rarr; {formatStatusLabel(entry.new_status)}
              </>
            ) : (
              formatStatusLabel(entry.new_status)
            )}
          </div>
          <div className="timeline-entry-meta">
            {entry.changed_by_name} &middot; {new Date(entry.created_at).toLocaleString()}
          </div>
          {entry.reason && <p className="timeline-entry-reason">{entry.reason}</p>}
        </li>
      ))}
    </ol>
  );
}

export default ComplaintTimeline;
