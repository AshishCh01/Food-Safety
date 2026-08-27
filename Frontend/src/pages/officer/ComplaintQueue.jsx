import { useEffect, useState } from 'react';
import ComplaintCard from '../../components/complaint/ComplaintCard';
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

  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <section>
      <h1>District Complaint Queue</h1>

      <div className="filter-row">
        <label htmlFor="status-filter">
          Status
          <select
            id="status-filter"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under review</option>
            <option value="needs_information">Needs information</option>
            <option value="verified">Verified</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>

        <label htmlFor="priority-filter">
          Priority
          <select
            id="priority-filter"
            value={priority}
            onChange={(event) => {
              setPriority(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}

      {result && result.items.length === 0 && <p>No complaints in the queue.</p>}

      <div className="complaint-list">
        {result?.items.map((complaint) => (
          <ComplaintCard key={complaint.id} complaint={complaint} linkTo={`/officer/complaints/${complaint.id}`} />
        ))}
      </div>

      {result && result.total > PAGE_SIZE && (
        <div className="pagination">
          <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button type="button" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      )}
    </section>
  );
}

export default ComplaintQueue;
