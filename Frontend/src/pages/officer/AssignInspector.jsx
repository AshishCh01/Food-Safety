import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { assignInspector, getDistrictComplaint, listInspectors } from '../../services/complaintService';

function AssignInspector() {
  const { complaintId } = useParams();
  const { getAccessToken } = useAuth();
  const navigate = useNavigate();
  const [complaint, setComplaint] = useState(null);
  const [inspectors, setInspectors] = useState([]);
  const [inspectorStaffId, setInspectorStaffId] = useState('');
  const [dueAt, setDueAt] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([getDistrictComplaint(complaintId, token), listInspectors(token)])
      .then(([complaintData, inspectorList]) => {
        setComplaint(complaintData);
        setInspectors(inspectorList);
      })
      .catch((err) => setError(err.message));
  }, [complaintId, getAccessToken]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await assignInspector(
        complaintId,
        { inspectorStaffId, dueAt: dueAt ? new Date(dueAt).toISOString() : null, notes },
        getAccessToken()
      );
      navigate(`/officer/complaints/${complaintId}`, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!complaint) {
    return error ? <p className="form-error">{error}</p> : <p>Loading...</p>;
  }

  return (
    <section>
      <h1>Assign an inspector</h1>
      <p>
        {complaint.complaint_number} &middot; {complaint.title}
      </p>

      {inspectors.length === 0 ? (
        <p>No active inspectors are available in your district.</p>
      ) : (
        <form onSubmit={handleSubmit} className="status-update-form">
          <label htmlFor="inspector-select">
            Inspector
            <select
              id="inspector-select"
              value={inspectorStaffId}
              onChange={(event) => setInspectorStaffId(event.target.value)}
              required
            >
              <option value="">Select an inspector</option>
              {inspectors.map((inspector) => (
                <option key={inspector.id} value={inspector.id}>
                  {inspector.full_name} ({inspector.employee_code})
                </option>
              ))}
            </select>
          </label>
          <label htmlFor="due-at">
            Due date (optional)
            <input id="due-at" type="date" value={dueAt} onChange={(event) => setDueAt(event.target.value)} />
          </label>
          <label htmlFor="assignment-notes">
            Notes (optional)
            <textarea id="assignment-notes" value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
          </label>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={!inspectorStaffId || isSubmitting}>
            {isSubmitting ? 'Assigning...' : 'Assign inspector'}
          </button>
        </form>
      )}
    </section>
  );
}

export default AssignInspector;
