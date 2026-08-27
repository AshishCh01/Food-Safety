import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ComplaintCard from '../../components/complaint/ComplaintCard';
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

  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <section>
      <div className="page-header">
        <h1>My complaints</h1>
        <Link to="/citizen/complaints/new">New complaint</Link>
      </div>

      <label htmlFor="status-filter">
        Status
        <select id="status-filter" value={status} onChange={handleStatusChange}>
          <option value="">All</option>
          <option value="submitted">Submitted</option>
          <option value="under_review">Under review</option>
          <option value="needs_information">Needs information</option>
          <option value="verified">Verified</option>
          <option value="rejected">Rejected</option>
        </select>
      </label>

      {error && <p className="form-error">{error}</p>}

      {result && result.items.length === 0 && <p>No complaints found.</p>}

      <div className="complaint-list">
        {result?.items.map((complaint) => (
          <ComplaintCard key={complaint.id} complaint={complaint} linkTo={`/citizen/complaints/${complaint.id}`} />
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

export default MyComplaints;
