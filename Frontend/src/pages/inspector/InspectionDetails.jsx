import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import { formatStatusLabel } from '../../utils/complaintStatus';
import EvidenceUploader from '../../components/complaint/EvidenceUploader';
import EvidenceAnalysisPanel from '../../components/agent/EvidenceAnalysisPanel';
import AssistantChat from '../../components/agent/AssistantChat';
import FindingForm from '../../components/inspection/FindingForm';
import FindingList from '../../components/inspection/FindingList';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Alert from '../../components/ui/Alert';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import DetailGrid from '../../components/ui/DetailGrid';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import { useAuth } from '../../hooks/useAuth';
import {
  createAssistantConversation,
  getAssistantConversation,
  getInspectionEvidenceAnalysis,
  listAssistantConversations,
  runInspectionEvidenceAnalysis,
  sendAssistantMessage,
} from '../../services/agentService';
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
  const [evidenceAnalyses, setEvidenceAnalyses] = useState({});
  const [analyzingEvidenceId, setAnalyzingEvidenceId] = useState(null);
  const [evidenceAnalysisErrors, setEvidenceAnalysisErrors] = useState({});
  const [assistantConversation, setAssistantConversation] = useState(null);
  const [isAssistantLoading, setIsAssistantLoading] = useState(false);
  const [isAssistantSending, setIsAssistantSending] = useState(false);
  const [assistantError, setAssistantError] = useState(null);

  const load = useCallback(() => {
    const token = getAccessToken();
    let inspectionId = null;
    getAssignment(assignmentId, token)
      .then((data) => {
        setAssignment(data);
        inspectionId = data.inspection ? data.inspection.id : null;
        return inspectionId ? listInspectionEvidence(inspectionId, token) : Promise.resolve([]);
      })
      .then((evidenceData) => {
        setEvidence(evidenceData);
        if (!inspectionId || evidenceData.length === 0) {
          return [];
        }
        return Promise.all(
          evidenceData.map((item) =>
            getInspectionEvidenceAnalysis(inspectionId, item.id, token)
              .then((result) => [item.id, result])
              .catch(() => [item.id, null]),
          ),
        );
      })
      .then((entries) => setEvidenceAnalyses(Object.fromEntries(entries)))
      .catch((err) => setError(err.message));
  }, [assignmentId, getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const inspectionId = assignment?.inspection?.id;
    if (!inspectionId || assistantConversation) return;

    let cancelled = false;
    setIsAssistantLoading(true);
    const token = getAccessToken();
    listAssistantConversations(token, { inspectionId })
      .then((result) =>
        result.items.length > 0
          ? getAssistantConversation(result.items[0].id, token)
          : createAssistantConversation(token, { inspectionId }),
      )
      .then((data) => {
        if (!cancelled) setAssistantConversation(data);
      })
      .catch((err) => {
        if (!cancelled) setAssistantError(err.message);
      })
      .finally(() => {
        if (!cancelled) setIsAssistantLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assignment?.inspection?.id]);

  async function handleSendAssistantMessage(question) {
    if (!assistantConversation) return;
    setAssistantError(null);
    setIsAssistantSending(true);
    try {
      const token = getAccessToken();
      await sendAssistantMessage(assistantConversation.id, question, token);
      const refreshed = await getAssistantConversation(assistantConversation.id, token);
      setAssistantConversation(refreshed);
    } catch (err) {
      setAssistantError(err.message);
    } finally {
      setIsAssistantSending(false);
    }
  }

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
      await addFinding(assignment.inspection.id, { ...form, compliant: !!form.compliant }, getAccessToken());
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

  async function handleAnalyzeEvidence(evidenceId, { force = false } = {}) {
    setEvidenceAnalysisErrors((prev) => ({ ...prev, [evidenceId]: null }));
    setAnalyzingEvidenceId(evidenceId);
    try {
      const result = await runInspectionEvidenceAnalysis(assignment.inspection.id, evidenceId, getAccessToken(), {
        force,
      });
      setEvidenceAnalyses((prev) => ({ ...prev, [evidenceId]: result }));
    } catch (err) {
      setEvidenceAnalysisErrors((prev) => ({ ...prev, [evidenceId]: err.message }));
    } finally {
      setAnalyzingEvidenceId(null);
    }
  }

  function renderEvidenceAnalysis(item) {
    return (
      <div className="mt-3">
        <EvidenceAnalysisPanel
          evidenceItem={item}
          analysis={evidenceAnalyses[item.id]}
          isRunning={analyzingEvidenceId === item.id}
          error={evidenceAnalysisErrors[item.id]}
          onRun={() => handleAnalyzeEvidence(item.id, { force: !!evidenceAnalyses[item.id] })}
        />
      </div>
    );
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
    return (
      <ContentContainer className="max-w-3xl">
        {error ? <ErrorState message={error} /> : <Skeleton.List rows={5} />}
      </ContentContainer>
    );
  }

  const { complaint, inspection } = assignment;

  return (
    <ContentContainer className="max-w-3xl">
      <PageHeader
        title={complaint.title}
        breadcrumbs={[{ label: 'Assigned complaints', path: '/inspector/assignments' }, { label: complaint.complaint_number }]}
        actions={<ComplaintStatus status={complaint.status} />}
      />

      <Card>
        <DetailGrid>
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
        </DetailGrid>
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Description</Card.Title>
        </Card.Header>
        <p className="text-sm text-slate-700">{complaint.description}</p>
        {complaint.business && (
          <p className="mt-2 text-sm text-slate-600">
            {complaint.business.business_name} &middot; {complaint.business.address}
          </p>
        )}
      </Card>

      {error && <Alert tone="danger">{error}</Alert>}

      {!inspection && (
        <Card>
          <Card.Header>
            <Card.Title>Inspection</Card.Title>
          </Card.Header>
          <InspectionForm mode="create" onSubmit={handleCreateInspection} isSubmitting={isSubmitting} />
        </Card>
      )}

      {inspection && (
        <>
          <Card>
            <Card.Header>
              <Card.Title>Inspection</Card.Title>
              {inspection.inspection_status === 'scheduled' && (
                <Button size="sm" onClick={handleStart} disabled={isSubmitting}>
                  Begin inspection
                </Button>
              )}
            </Card.Header>
            <p className="text-sm text-slate-700">Status: {formatStatusLabel(inspection.inspection_status)}</p>
          </Card>

          {inspection.inspection_status !== 'completed' && (
            <>
              <Card>
                <Card.Header>
                  <Card.Title>Findings</Card.Title>
                </Card.Header>
                <FindingList findings={inspection.findings} />
                <div className="mt-4">
                  <FindingForm onSubmit={handleAddFinding} isSubmitting={isSubmitting} />
                </div>
              </Card>

              <Card>
                <Card.Header>
                  <Card.Title>Evidence</Card.Title>
                </Card.Header>
                <EvidenceUploader evidence={evidence} onUpload={handleUploadEvidence} renderExtra={renderEvidenceAnalysis} />
              </Card>
            </>
          )}

          {inspection.inspection_status === 'in_progress' && (
            <Card>
              <Card.Header>
                <Card.Title>Complete inspection</Card.Title>
              </Card.Header>
              <InspectionForm mode="complete" onSubmit={handleComplete} isSubmitting={isSubmitting} />
            </Card>
          )}

          {inspection.inspection_status === 'completed' && (
            <>
              <Card>
                <Card.Header>
                  <Card.Title>Findings</Card.Title>
                </Card.Header>
                <FindingList findings={inspection.findings} />
              </Card>
              <Card>
                <Card.Header>
                  <Card.Title>Evidence</Card.Title>
                </Card.Header>
                <EvidenceUploader evidence={evidence} readOnly renderExtra={renderEvidenceAnalysis} />
              </Card>
              <Card>
                <Card.Header>
                  <Card.Title>Outcome</Card.Title>
                </Card.Header>
                <p className="text-sm text-slate-700">
                  <strong className="font-medium text-slate-900">Summary:</strong> {inspection.summary}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  <strong className="font-medium text-slate-900">Recommended action:</strong> {inspection.action_recommended}
                </p>
              </Card>
            </>
          )}

          <Card>
            <Card.Header>
              <Card.Title>Inspector Assistant</Card.Title>
            </Card.Header>
            <AssistantChat
              messages={assistantConversation ? assistantConversation.messages : []}
              onSend={handleSendAssistantMessage}
              isSending={isAssistantSending}
              error={assistantError}
              isLoading={isAssistantLoading}
            />
          </Card>
        </>
      )}
    </ContentContainer>
  );
}

export default InspectionDetails;
