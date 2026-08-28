import { Link } from 'react-router-dom';
import Badge from '../ui/Badge';
import { PRIORITIES, configFor } from '../../utils/statusConfig';
import { formatDate } from '../../utils/formatters';
import ComplaintStatus from './ComplaintStatus';

function ComplaintCard({ complaint, linkTo }) {
  const priority = configFor(PRIORITIES, complaint.priority);
  return (
    <Link
      to={linkTo}
      className="block rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-brand-300 hover:bg-brand-50/30"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-xs text-slate-500">{complaint.complaint_number}</span>
        <ComplaintStatus status={complaint.status} />
      </div>
      <h3 className="mt-1.5 font-medium text-slate-900">{complaint.title}</h3>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span>{complaint.category_name}</span>
        <span aria-hidden="true">&middot;</span>
        <span>{complaint.district_name}</span>
        <Badge tone={priority.tone}>{priority.label}</Badge>
      </div>
      <time className="mt-2 block text-xs text-slate-400">{formatDate(complaint.created_at)}</time>
    </Link>
  );
}

export default ComplaintCard;
