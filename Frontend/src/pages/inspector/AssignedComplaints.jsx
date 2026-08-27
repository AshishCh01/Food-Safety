import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import { useAuth } from '../../hooks/useAuth';
import { listAssignments } from '../../services/inspectionService';

const PAGE_SIZE = 10;

function AssignedComplaints() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    listAssignments(token, { status: status || undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, status, page]);

  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <section>
      <h1>My Assigned Complaints</h1>

      <label htmlFor="assignment-status-filter">
        Status
        <select
          id="assignment-status-filter"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In progress</option>
          <option value="completed">Completed</option>
        </select>
      </label>

      {error && <p className="form-error">{error}</p>}

      {result && result.items.length === 0 && <p>No assignments found.</p>}

      <div className="complaint-list">
        {result?.items.map((assignment) => (
          <Link key={assignment.id} to={`/inspector/assignments/${assignment.id}`} className="complaint-card">
            <div className="complaint-card-header">
              <span className="complaint-number">{assignment.complaint_number}</span>
              <ComplaintStatus status={assignment.status} />
            </div>
            <h3>{assignment.complaint_title}</h3>
            {assignment.due_at && (
              <span className="complaint-card-date">Due {new Date(assignment.due_at).toLocaleDateString()}</span>
            )}
          </Link>
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

export default AssignedComplaints;
