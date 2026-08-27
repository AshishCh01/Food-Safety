import { Link } from 'react-router-dom';
import ComplaintStatus from './ComplaintStatus';

function ComplaintCard({ complaint, linkTo }) {
  return (
    <Link to={linkTo} className="complaint-card">
      <div className="complaint-card-header">
        <span className="complaint-number">{complaint.complaint_number}</span>
        <ComplaintStatus status={complaint.status} />
      </div>
      <h3>{complaint.title}</h3>
      <div className="complaint-card-meta">
        <span>{complaint.category_name}</span>
        <span>{complaint.district_name}</span>
        <span className={`priority-tag priority-${complaint.priority}`}>{complaint.priority}</span>
      </div>
      <time className="complaint-card-date">{new Date(complaint.created_at).toLocaleString()}</time>
    </Link>
  );
}

export default ComplaintCard;
