import { formatStatusLabel, variantForStatus } from '../../utils/complaintStatus';

function ComplaintStatus({ status }) {
  return <span className={`status-badge ${variantForStatus(status)}`}>{formatStatusLabel(status)}</span>;
}

export default ComplaintStatus;
