import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import { formatStatusLabel } from '../../utils/complaintStatus';
import { formatDate, formatDateTime } from '../../utils/formatters';
import { PRIORITIES, configFor } from '../../utils/statusConfig';
import ComplaintTimeline from '../../components/complaint/ComplaintTimeline';
import EvidenceUploader from '../../components/complaint/EvidenceUploader';
import FindingList from '../../components/inspection/FindingList';
import LocationMap from '../../components/map/LocationMap';
import ComplaintTriagePanel from '../../components/agent/ComplaintTriagePanel';
import EvidenceAnalysisPanel from '../../components/agent/EvidenceAnalysisPanel';
import InvestigationBriefPanel from '../../components/agent/InvestigationBriefPanel';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Alert from '../../components/ui/Alert';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import DetailGrid from '../../components/ui/DetailGrid';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import Textarea from '../../components/ui/Textarea';
import { useAuth } from '../../hooks/useAuth';
import {
  getComplaintEvidenceAnalysis,
  getComplaintInvestigation,
  getComplaintTriage,
  runComplaintEvidenceAnalysis,
  runComplaintInvestigation,
  runComplaintTriage,
} from '../../services/agentService';
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
  submitted: ['under_review', 'verified', 'rejected', 'duplicate', 'insufficient_evidence'],
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
  const [triage, setTriage] = useState(null);
  const [nextStatus, setNextStatus] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [triageError, setTriageError] = useState(null);
  const [isTriageRunning, setIsTriageRunning] = useState(false);
  const [evidenceAnalyses, setEvidenceAnalyses] = useState({});
  const [analyzingEvidenceId, setAnalyzingEvidenceId] = useState(null);
  const [evidenceAnalysisErrors, setEvidenceAnalysisErrors] = useState({});
  const [investigation, setInvestigation] = useState(null);
  const [investigationError, setInvestigationError] = useState(null);
  const [isInvestigationRunning, setIsInvestigationRunning] = useState(false);

  const load = useCallback(() => {
    const token = getAccessToken();
    Promise.all([
      getDistrictComplaint(complaintId, token),
      getDistrictComplaintTimeline(complaintId, token),
      listDistrictComplaintEvidence(complaintId, token),
      getComplaintAssignment(complaintId, token).catch(() => null),
      getComplaintInspection(complaintId, token).catch(() => null),
      getComplaintTriage(complaintId, token).catch(() => null),
      getComplaintInvestigation(complaintId, token).catch(() => null),
    ])
      .then(([complaintData, timelineData, evidenceData, assignmentData, inspectionData, triageData, investigationData]) => {
        setComplaint(complaintData);
        setTimeline(timelineData);
        setEvidence(evidenceData);
        setAssignment(assignmentData);
        setInspection(inspectionData);
        setTriage(triageData);
        setInvestigation(investigationData);
        setNextStatus('');

        return Promise.all(
          evidenceData.map((item) =>
            getComplaintEvidenceAnalysis(complaintId, item.id, token)
              .then((result) => [item.id, result])
              .catch(() => [item.id, null]),
          ),
        );
      })
      .then((entries) => {
        if (entries) {
          setEvidenceAnalyses(Object.fromEntries(entries));
        }
      })
      .catch((err) => setError(err.message));
  }, [complaintId, getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRunTriage() {
    setTriageError(null);
    setIsTriageRunning(true);
    try {
      const result = await runComplaintTriage(complaintId, getAccessToken());
      setTriage(result);
    } catch (err) {
      setTriageError(err.message);
    } finally {
      setIsTriageRunning(false);
    }
  }

  async function handleRunInvestigation() {
    setInvestigationError(null);
    setIsInvestigationRunning(true);
    try {
      const result = await runComplaintInvestigation(complaintId, getAccessToken(), { force: !!investigation });
      setInvestigation(result);
    } catch (err) {
      setInvestigationError(err.message);
    } finally {
      setIsInvestigationRunning(false);
    }
  }

  async function handleAnalyzeEvidence(evidenceId, { force = false } = {}) {
    setEvidenceAnalysisErrors((prev) => ({ ...prev, [evidenceId]: null }));
    setAnalyzingEvidenceId(evidenceId);
    try {
      const result = await runComplaintEvidenceAnalysis(complaintId, evidenceId, getAccessToken(), { force });
      setEvidenceAnalyses((prev) => ({ ...prev, [evidenceId]: result }));
    } catch (err) {
      setEvidenceAnalysisErrors((prev) => ({ ...prev, [evidenceId]: err.message }));
    } finally {
      setAnalyzingEvidenceId(null);
    }
  }

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
    return (
      <ContentContainer className="max-w-4xl">
        {error ? <ErrorState message={error} /> : <Skeleton.List rows={6} />}
      </ContentContainer>
    );
  }

  const availableTransitions = ALLOWED_TRANSITIONS[complaint.status] || [];
  const priority = configFor(PRIORITIES, complaint.priority);

  return (
    <ContentContainer className="max-w-4xl">
      <PageHeader
        title={complaint.title}
        breadcrumbs={[{ label: 'Complaint queue', path: '/officer/complaints' }, { label: complaint.complaint_number }]}
        actions={<ComplaintStatus status={complaint.status} />}
      />

      <Card>
        <DetailGrid>
          <dt>Category</dt>
          <dd>{complaint.category_name}</dd>
          <dt>Priority</dt>
          <dd>
            <Badge tone={priority.tone}>{priority.label}</Badge>
          </dd>
          <dt>Submitted by</dt>
          <dd>{complaint.submitted_by_name}</dd>
          <dt>Reported at</dt>
          <dd>{formatDateTime(complaint.reported_at)}</dd>
          {complaint.address_line && (
            <>
              <dt>Location</dt>
              <dd>{complaint.address_line}</dd>
            </>
          )}
        </DetailGrid>
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Description</Card.Title>
        </Card.Header>
        <p className="text-sm text-slate-700">{complaint.description}</p>
      </Card>

      {complaint.business && (
        <Card>
          <Card.Header>
            <Card.Title>Business</Card.Title>
          </Card.Header>
          <p className="text-sm text-slate-700">
            {complaint.business.business_name} &middot; {complaint.business.address}
          </p>
          {complaint.business.latitude !== null && complaint.business.longitude !== null && (
            <div className="mt-3">
              <LocationMap
                latitude={complaint.business.latitude}
                longitude={complaint.business.longitude}
                label={complaint.business.business_name}
              />
            </div>
          )}
        </Card>
      )}

      {complaint.latitude !== null && complaint.longitude !== null && (
        <Card>
          <Card.Header>
            <Card.Title>Location</Card.Title>
          </Card.Header>
          <LocationMap latitude={complaint.latitude} longitude={complaint.longitude} label={complaint.title} />
        </Card>
      )}

      <ComplaintTriagePanel triage={triage} isRunning={isTriageRunning} error={triageError} onRun={handleRunTriage} />

      <Card>
        <Card.Header>
          <Card.Title>Evidence</Card.Title>
        </Card.Header>
        <EvidenceUploader
          evidence={evidence}
          readOnly
          renderExtra={(item) => (
            <div className="mt-3">
              <EvidenceAnalysisPanel
                evidenceItem={item}
                analysis={evidenceAnalyses[item.id]}
                isRunning={analyzingEvidenceId === item.id}
                error={evidenceAnalysisErrors[item.id]}
                onRun={() => handleAnalyzeEvidence(item.id, { force: !!evidenceAnalyses[item.id] })}
              />
            </div>
          )}
        />
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Inspection assignment</Card.Title>
        </Card.Header>
        {complaint.status === 'verified' && !assignment && (
          <Link to={`/officer/complaints/${complaintId}/assign`}>
            <Button variant="secondary" size="sm">
              Assign an inspector
            </Button>
          </Link>
        )}
        {assignment && (
          <DetailGrid>
            <dt>Inspector</dt>
            <dd>{assignment.inspector_name}</dd>
            <dt>Assignment status</dt>
            <dd>{formatStatusLabel(assignment.status)}</dd>
            {assignment.due_at && (
              <>
                <dt>Due</dt>
                <dd>{formatDate(assignment.due_at)}</dd>
              </>
            )}
            {assignment.notes && (
              <>
                <dt>Notes</dt>
                <dd>{assignment.notes}</dd>
              </>
            )}
          </DetailGrid>
        )}
        {!assignment && complaint.status !== 'verified' && (
          <p className="text-sm text-slate-500">No inspector assigned yet.</p>
        )}
      </Card>

      {inspection && (
        <Card>
          <Card.Header>
            <Card.Title>Inspection results</Card.Title>
          </Card.Header>
          <p className="text-sm text-slate-700">Status: {formatStatusLabel(inspection.inspection_status)}</p>
          {inspection.summary && <p className="mt-1 text-sm text-slate-700">{inspection.summary}</p>}
          {inspection.action_recommended && (
            <p className="mt-1 text-sm text-slate-700">
              <strong className="font-medium text-slate-900">Recommended action:</strong> {inspection.action_recommended}
            </p>
          )}
          <div className="mt-3">
            <FindingList findings={inspection.findings} />
          </div>
        </Card>
      )}

      <InvestigationBriefPanel
        brief={investigation}
        isRunning={isInvestigationRunning}
        error={investigationError}
        onRun={handleRunInvestigation}
      />

      <Card>
        <Card.Header>
          <Card.Title>Update status</Card.Title>
        </Card.Header>
        {availableTransitions.length === 0 ? (
          <p className="text-sm text-slate-500">No further status updates are available for this complaint in this phase.</p>
        ) : (
          <form onSubmit={handleStatusUpdate} className="flex flex-col gap-4">
            <FormField label="New status" htmlFor="next-status">
              <Select id="next-status" value={nextStatus} onChange={(event) => setNextStatus(event.target.value)}>
                <option value="">Select a status</option>
                {availableTransitions.map((status) => (
                  <option key={status} value={status}>
                    {formatStatusLabel(status)}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="Reason" htmlFor="status-reason" hint="Optional">
              <Textarea id="status-reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={3} />
            </FormField>
            {error && <Alert tone="danger">{error}</Alert>}
            <Button type="submit" disabled={!nextStatus} loading={isSubmitting} className="self-start">
              {isSubmitting ? 'Updating…' : 'Update status'}
            </Button>
          </form>
        )}
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Timeline</Card.Title>
        </Card.Header>
        <ComplaintTimeline entries={timeline} />
      </Card>
    </ContentContainer>
  );
}

export default ComplaintReview;
