import Badge from '../ui/Badge';
import { COMPLAINT_STATUSES, configFor } from '../../utils/statusConfig';

function ComplaintStatus({ status }) {
  const { label, tone } = configFor(COMPLAINT_STATUSES, status);
  return <Badge tone={tone}>{label}</Badge>;
}

export default ComplaintStatus;
