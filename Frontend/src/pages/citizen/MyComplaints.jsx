import { useEffect, useState } from 'react';
import { PlusCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import ComplaintCard from '../../components/complaint/ComplaintCard';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Pagination from '../../components/ui/Pagination';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import { COMPLAINT_STATUSES } from '../../utils/statusConfig';
import { useAuth } from '../../hooks/useAuth';
import { listMyComplaints } from '../../services/complaintService';

const PAGE_SIZE = 10;

function MyComplaints() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    listMyComplaints(token, { status: status || undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, status, page]);

  function handleStatusChange(event) {
    setStatus(event.target.value);
    setPage(1);
  }

  return (
    <ContentContainer>
      <PageHeader
        title="My complaints"
        actions={
          <Link to="/citizen/complaints/new">
            <Button>
              <PlusCircle className="size-4" aria-hidden="true" />
              New complaint
            </Button>
          </Link>
        }
      />

      <FormField label="Status" htmlFor="status-filter" className="max-w-xs">
        <Select id="status-filter" value={status} onChange={handleStatusChange}>
          <option value="">All</option>
          {COMPLAINT_STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>
      </FormField>

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={4} />}

      {result && result.items.length === 0 && (
        <EmptyState title="No complaints found." description="Try a different status filter, or report a new issue." />
      )}

      <div className="flex flex-col gap-3">
        {result?.items.map((complaint) => (
          <ComplaintCard key={complaint.id} complaint={complaint} linkTo={`/citizen/complaints/${complaint.id}`} />
        ))}
      </div>

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default MyComplaints;
