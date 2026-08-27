import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import { formatStatusLabel } from '../../utils/complaintStatus';
import EvidenceUploader from '../../components/complaint/EvidenceUploader';
import FindingForm from '../../components/inspection/FindingForm';
import FindingList from '../../components/inspection/FindingList';
import { useAuth } from '../../hooks/useAuth';
import {
  addFinding,
  completeInspection,
  createInspection,
  getAssignment,
  listInspectionEvidence,
  startInspection,
  uploadInspectionEvidence,
} from '../../services/inspectionService';
import InspectionForm from './InspectionForm';

function InspectionDetails() {
  const { assignmentId } = useParams();
  const { getAccessToken } = useAuth();
  const [assignment, setAssignment] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(() => {
    const token = getAccessToken();
    getAssignment(assignmentId, token)
      .then((data) => {
        setAssignment(data);
        return data.inspection
          ? listInspectionEvidence(data.inspection.id, token)
          : Promise.resolve([]);
      })
      .then(setEvidence)
      .catch((err) => setError(err.message));
  }, [assignmentId, getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreateInspection({ scheduledAt }) {
    setError(null);
    setIsSubmitting(true);
    try {
      await createInspection({ complaintId: assignment.complaint_id, scheduledAt }, getAccessToken());
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleStart() {
    setError(null);
    setIsSubmitting(true);
    try {
      await startInspection(assignment.inspection.id, getAccessToken());
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleAddFinding(form) {
    setIsSubmitting(true);
    try {
      await addFinding(
        assignment.inspection.id,
        { ...form, compliant: !!form.compliant },
        getAccessToken()
      );
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUploadEvidence(file) {
    await uploadInspectionEvidence(assignment.inspection.id, file, getAccessToken());
    const updated = await listInspectionEvidence(assignment.inspection.id, getAccessToken());
    setEvidence(updated);
  }

  async function handleComplete({ summary, actionRecommended }) {
    setError(null);
    setIsSubmitting(true);
    try {
      await completeInspection(assignment.inspection.id, { summary, actionRecommended }, getAccessToken());
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!assignment) {
    return error ? <p className="form-error">{error}</p> : <p>Loading...</p>;
  }

  const { complaint, inspection } = assignment;

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
        </>
      )}

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <h2>Inspection</h2>
      {!inspection && <InspectionForm mode="create" onSubmit={handleCreateInspection} isSubmitting={isSubmitting} />}

      {inspection && (
        <>
          <p>Status: {formatStatusLabel(inspection.inspection_status)}</p>

          {inspection.inspection_status === 'scheduled' && (
            <button type="button" onClick={handleStart} disabled={isSubmitting}>
              Begin inspection
            </button>
          )}

          {inspection.inspection_status !== 'completed' && (
            <>
              <h3>Findings</h3>
              <FindingList findings={inspection.findings} />
              <FindingForm onSubmit={handleAddFinding} isSubmitting={isSubmitting} />

              <h3>Evidence</h3>
              <EvidenceUploader evidence={evidence} onUpload={handleUploadEvidence} />
            </>
          )}

          {inspection.inspection_status === 'in_progress' && (
            <>
              <h3>Complete inspection</h3>
              <InspectionForm mode="complete" onSubmit={handleComplete} isSubmitting={isSubmitting} />
            </>
          )}

          {inspection.inspection_status === 'completed' && (
            <>
              <h3>Findings</h3>
              <FindingList findings={inspection.findings} />
              <h3>Evidence</h3>
              <EvidenceUploader evidence={evidence} readOnly />
              <p>
                <strong>Summary:</strong> {inspection.summary}
              </p>
              <p>
                <strong>Recommended action:</strong> {inspection.action_recommended}
              </p>
            </>
          )}
        </>
      )}
    </section>
  );
}

export default InspectionDetails;
