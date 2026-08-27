import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import { formatStatusLabel } from '../../utils/complaintStatus';
import ComplaintTimeline from '../../components/complaint/ComplaintTimeline';
import EvidenceUploader from '../../components/complaint/EvidenceUploader';
import FindingList from '../../components/inspection/FindingList';
import LocationMap from '../../components/map/LocationMap';
import { useAuth } from '../../hooks/useAuth';
import {
  getComplaintAssignment,
  getComplaintInspection,
  getDistrictComplaint,
  getDistrictComplaintTimeline,
  listDistrictComplaintEvidence,
  updateComplaintStatus,
} from '../../services/complaintService';

// Mirrors app.services.complaint_service.ALLOWED_TRANSITIONS on the backend
// (the source of truth) - kept here only to drive the dropdown; the server
// re-validates every transition regardless. Assignment/inspection-driven
// transitions (verified->assigned->...->inspection_completed) are not
// listed here since they only happen through their own dedicated actions.
const ALLOWED_TRANSITIONS = {
  submitted: ['under_review', 'rejected', 'duplicate', 'insufficient_evidence'],
  under_review: ['needs_information', 'verified', 'rejected', 'duplicate', 'insufficient_evidence'],
  needs_information: ['under_review', 'rejected'],
  inspection_completed: ['action_in_progress', 'resolved', 'closed'],
  action_in_progress: ['resolved', 'closed'],
  resolved: ['closed'],
};

function ComplaintReview() {
  const { complaintId } = useParams();
  const { getAccessToken } = useAuth();
  const [complaint, setComplaint] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [assignment, setAssignment] = useState(null);
  const [inspection, setInspection] = useState(null);
  const [nextStatus, setNextStatus] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(() => {
    const token = getAccessToken();
    Promise.all([
      getDistrictComplaint(complaintId, token),
      getDistrictComplaintTimeline(complaintId, token),
      listDistrictComplaintEvidence(complaintId, token),
      getComplaintAssignment(complaintId, token).catch(() => null),
      getComplaintInspection(complaintId, token).catch(() => null),
    ])
      .then(([complaintData, timelineData, evidenceData, assignmentData, inspectionData]) => {
        setComplaint(complaintData);
        setTimeline(timelineData);
        setEvidence(evidenceData);
        setAssignment(assignmentData);
        setInspection(inspectionData);
        setNextStatus('');
      })
      .catch((err) => setError(err.message));
  }, [complaintId, getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStatusUpdate(event) {
    event.preventDefault();
    if (!nextStatus) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await updateComplaintStatus(complaintId, { status: nextStatus, reason }, getAccessToken());
      setReason('');
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!complaint) {
    return error ? <p className="form-error">{error}</p> : <p>Loading...</p>;
  }

  const availableTransitions = ALLOWED_TRANSITIONS[complaint.status] || [];

  return (
    <section>
      <div className="page-header">
        <h1>{complaint.title}</h1>
        <ComplaintStatus status={complaint.status} />
      </div>
      <p className="complaint-number">{complaint.complaint_number}</p>

      <dl className="complaint-detail-grid">
        <dt>Category</dt>
        <dd>{complaint.category_name}</dd>
        <dt>Priority</dt>
        <dd>{complaint.priority}</dd>
        <dt>Submitted by</dt>
        <dd>{complaint.submitted_by_name}</dd>
        <dt>Reported at</dt>
        <dd>{new Date(complaint.reported_at).toLocaleString()}</dd>
        {complaint.address_line && (
          <>
            <dt>Location</dt>
            <dd>{complaint.address_line}</dd>
          </>
        )}
      </dl>

      <h2>Description</h2>
      <p>{complaint.description}</p>

      {complaint.business && (
        <>
          <h2>Business</h2>
          <p>
            {complaint.business.business_name} &middot; {complaint.business.address}
          </p>
          {complaint.business.latitude !== null && complaint.business.longitude !== null && (
            <LocationMap
              latitude={complaint.business.latitude}
              longitude={complaint.business.longitude}
              label={complaint.business.business_name}
            />
          )}
        </>
      )}

      {complaint.latitude !== null && complaint.longitude !== null && (
        <>
          <h2>Location</h2>
          <LocationMap latitude={complaint.latitude} longitude={complaint.longitude} label={complaint.title} />
        </>
      )}

      <h2>Evidence</h2>
      <EvidenceUploader evidence={evidence} readOnly />

      <h2>Inspection assignment</h2>
      {complaint.status === 'verified' && !assignment && (
        <p>
          <Link to={`/officer/complaints/${complaintId}/assign`}>Assign an inspector</Link>
        </p>
      )}
      {assignment && (
        <dl className="complaint-detail-grid">
          <dt>Inspector</dt>
          <dd>{assignment.inspector_name}</dd>
          <dt>Assignment status</dt>
          <dd>{formatStatusLabel(assignment.status)}</dd>
          {assignment.due_at && (
            <>
              <dt>Due</dt>
              <dd>{new Date(assignment.due_at).toLocaleDateString()}</dd>
            </>
          )}
          {assignment.notes && (
            <>
              <dt>Notes</dt>
              <dd>{assignment.notes}</dd>
            </>
          )}
        </dl>
      )}

      {inspection && (
        <>
          <h2>Inspection results</h2>
          <p>Status: {formatStatusLabel(inspection.inspection_status)}</p>
          {inspection.summary && <p>{inspection.summary}</p>}
          {inspection.action_recommended && (
            <p>
              <strong>Recommended action:</strong> {inspection.action_recommended}
            </p>
          )}
          <FindingList findings={inspection.findings} />
        </>
      )}

      <h2>Update status</h2>
      {availableTransitions.length === 0 ? (
        <p>No further status updates are available for this complaint in this phase.</p>
      ) : (
        <form onSubmit={handleStatusUpdate} className="status-update-form">
          <label htmlFor="next-status">
            New status
            <select id="next-status" value={nextStatus} onChange={(event) => setNextStatus(event.target.value)}>
              <option value="">Select a status</option>
              {availableTransitions.map((status) => (
                <option key={status} value={status}>
                  {formatStatusLabel(status)}
                </option>
              ))}
            </select>
          </label>
          <label htmlFor="status-reason">
            Reason (optional)
            <textarea id="status-reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={3} />
          </label>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={!nextStatus || isSubmitting}>
            {isSubmitting ? 'Updating...' : 'Update status'}
          </button>
        </form>
      )}

      <h2>Timeline</h2>
      <ComplaintTimeline entries={timeline} />
    </section>
  );
}

export default ComplaintReview;
