import { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { listInspectionHistory } from '../../services/inspectionService';

const PAGE_SIZE = 10;

function InspectionHistory() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    listInspectionHistory(getAccessToken(), { page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, page]);

  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <section>
      <h1>Inspection History</h1>
      {error && <p className="form-error">{error}</p>}
      {result && result.items.length === 0 && <p>No completed inspections yet.</p>}

      <div className="complaint-list">
        {result?.items.map((inspection) => (
          <div key={inspection.id} className="complaint-card">
            <div className="complaint-card-header">
              <span className="complaint-number">{inspection.complaint_number}</span>
            </div>
            <span>Completed {new Date(inspection.completed_at).toLocaleString()}</span>
          </div>
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

export default InspectionHistory;
