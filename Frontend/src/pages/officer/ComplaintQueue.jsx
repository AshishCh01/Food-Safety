import { useEffect, useState } from 'react';
import ComplaintCard from '../../components/complaint/ComplaintCard';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Pagination from '../../components/ui/Pagination';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import { COMPLAINT_STATUSES, PRIORITIES } from '../../utils/statusConfig';
import { useAuth } from '../../hooks/useAuth';
import { listDistrictComplaints } from '../../services/complaintService';

const PAGE_SIZE = 10;

function ComplaintQueue() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    listDistrictComplaints(token, {
      status: status || undefined,
      priority: priority || undefined,
      page,
      pageSize: PAGE_SIZE,
    })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, status, priority, page]);

  return (
    <ContentContainer>
      <PageHeader title="District Complaint Queue" />

      <div className="flex flex-wrap gap-3">
        <FormField label="Status" htmlFor="status-filter" className="w-44">
          <Select
            id="status-filter"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            {COMPLAINT_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Priority" htmlFor="priority-filter" className="w-44">
          <Select
            id="priority-filter"
            value={priority}
            onChange={(event) => {
              setPriority(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            {PRIORITIES.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </Select>
        </FormField>
      </div>

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={5} />}

      {result && result.items.length === 0 && <EmptyState title="No complaints in the queue." />}

      <div className="flex flex-col gap-3">
        {result?.items.map((complaint) => (
          <ComplaintCard key={complaint.id} complaint={complaint} linkTo={`/officer/complaints/${complaint.id}`} />
        ))}
      </div>

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default ComplaintQueue;
