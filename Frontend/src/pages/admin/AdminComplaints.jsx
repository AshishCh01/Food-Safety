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
import { listAdminComplaints, listDistricts } from '../../services/complaintService';

const PAGE_SIZE = 10;

function AdminComplaints() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [districts, setDistricts] = useState([]);
  const [districtId, setDistrictId] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    listDistricts(getAccessToken())
      .then(setDistricts)
      .catch(console.error);
  }, [getAccessToken]);

  useEffect(() => {
    const token = getAccessToken();
    listAdminComplaints(token, {
      districtId: districtId || undefined,
      status: status || undefined,
      priority: priority || undefined,
      page,
      pageSize: PAGE_SIZE,
    })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, districtId, status, priority, page]);

  return (
    <ContentContainer>
      <PageHeader title="All Statewide Complaints" description="View all filed complaints across all districts." />

      <div className="flex flex-wrap gap-3">
        <FormField label="District" htmlFor="district-filter" className="w-44">
          <Select
            id="district-filter"
            value={districtId}
            onChange={(event) => {
              setDistrictId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All Districts</option>
            {districts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </FormField>

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

      {result && result.items.length === 0 && <EmptyState title="No complaints in the system." />}

      <div className="flex flex-col gap-3">
        {result?.items.map((complaint) => (
          <ComplaintCard key={complaint.id} complaint={complaint} linkTo={`/admin/complaints/${complaint.id}`} />
        ))}
      </div>

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default AdminComplaints;
