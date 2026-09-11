import { useCallback, useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import ComplaintTimeline from '../../components/complaint/ComplaintTimeline';
import EvidenceUploader from '../../components/complaint/EvidenceUploader';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import LocationMap from '../../components/map/LocationMap';
import Alert from '../../components/ui/Alert';
import Badge from '../../components/ui/Badge';
import Card from '../../components/ui/Card';
import DetailGrid from '../../components/ui/DetailGrid';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import { useAuth } from '../../hooks/useAuth';
import { formatDateTime } from '../../utils/formatters';
import { PRIORITIES, configFor } from '../../utils/statusConfig';
import {
  getComplaint,
  getComplaintTimeline,
  listEvidence,
  uploadEvidence,
  respondToClarification,
  listCitizenSamples,
  listCitizenLegalActions,
} from '../../services/complaintService';
import Button from '../../components/ui/Button';
import Textarea from '../../components/ui/Textarea';
import FormField from '../../components/ui/FormField';

function ComplaintDetails() {
  const { complaintId } = useParams();
  const { getAccessToken } = useAuth();
  const location = useLocation();
  const [complaint, setComplaint] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [samples, setSamples] = useState([]);
  const [legalActions, setLegalActions] = useState([]);
  const [error, setError] = useState(null);
  const [clarifyMessage, setClarifyMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(() => {
    const token = getAccessToken();
    Promise.all([
      getComplaint(complaintId, token),
      getComplaintTimeline(complaintId, token),
      listEvidence(complaintId, token),
      listCitizenSamples(complaintId, token).catch(() => []),
      listCitizenLegalActions(complaintId, token).catch(() => []),
    ])
      .then(([complaintData, timelineData, evidenceData, samplesData, legalData]) => {
        setComplaint(complaintData);
        setTimeline(timelineData);
        setEvidence(evidenceData);
        setSamples(samplesData);
        setLegalActions(legalData);
      })
      .catch((err) => setError(err.message));
  }, [complaintId, getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleUpload(file) {
    const token = getAccessToken();
    await uploadEvidence(complaintId, file, token);
    const evidenceData = await listEvidence(complaintId, token);
    setEvidence(evidenceData);
  }

  async function handleClarifySubmit(e) {
    e.preventDefault();
    if (!clarifyMessage.trim()) return;
    setIsSubmitting(true);
    try {
      await respondToClarification(complaintId, clarifyMessage, getAccessToken());
      setClarifyMessage('');
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (error) {
    return (
      <ContentContainer>
        <ErrorState message={error} />
      </ContentContainer>
    );
  }

  if (!complaint) {
    return (
      <ContentContainer>
        <Skeleton.List rows={5} />
      </ContentContainer>
    );
  }

  const priority = configFor(PRIORITIES, complaint.priority);

  return (
    <ContentContainer className="max-w-3xl">
      <PageHeader
        title={complaint.title}
        breadcrumbs={[{ label: 'My complaints', path: '/citizen/complaints' }, { label: complaint.complaint_number }]}
        actions={<ComplaintStatus status={complaint.status} />}
      />

      {location.state?.evidenceWarning && (
        <Alert tone="warning">Some evidence failed to upload: {location.state.evidenceWarning}</Alert>
      )}

      <Card>
        <DetailGrid>
          <dt>Category</dt>
          <dd>
            {complaint.category_name}
            {complaint.subcategory_name && ` > ${complaint.subcategory_name}`}
            {complaint.food_type && ` > ${complaint.food_type}`}
          </dd>
          <dt>Priority</dt>
          <dd>
            <Badge tone={priority.tone}>{priority.label}</Badge>
          </dd>
          <dt>District</dt>
          <dd>{complaint.district_name}</dd>
          {complaint.business?.business_type && (
            <>
              <dt>Concern</dt>
              <dd>{complaint.business.business_type}</dd>
            </>
          )}
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

      {complaint.status === 'insufficient_evidence' && (
        <Card className="border-brand-500 bg-brand-50">
          <Card.Header>
            <Card.Title className="text-brand-900">Information Requested</Card.Title>
          </Card.Header>
          <div className="p-4 sm:p-5">
            <p className="text-sm text-brand-800 mb-4">
              The reviewing officer has requested additional information or clarification regarding your complaint. Please provide the details below.
            </p>
            <form onSubmit={handleClarifySubmit} className="space-y-4">
              <FormField label="Your Response">
                <Textarea 
                  required
                  rows={4} 
                  value={clarifyMessage} 
                  onChange={(e) => setClarifyMessage(e.target.value)} 
                />
              </FormField>
              <Button type="submit" loading={isSubmitting}>
                Submit Response
              </Button>
            </form>
          </div>
        </Card>
      )}

      {samples.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Collected Samples</Card.Title>
          </Card.Header>
          <div className="p-4 sm:p-5">
            <ul className="space-y-3">
              {samples.map((s) => (
                <li key={s.id} className="text-sm text-slate-700 flex justify-between border-b pb-2 last:border-0">
                  <span>
                    <strong className="font-medium text-slate-900">{s.item_description}</strong> ({s.quantity} {s.unit})
                  </span>
                  <Badge tone={s.status === 'result_submitted' ? 'success' : 'neutral'}>
                    {s.status.replace('_', ' ')}
                  </Badge>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      {legalActions.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Legal Actions Taken</Card.Title>
          </Card.Header>
          <div className="p-4 sm:p-5">
            <ul className="space-y-4">
              {legalActions.map((a) => (
                <li key={a.id} className="text-sm text-slate-700 border-l-2 border-slate-200 pl-4">
                  <div className="flex items-center gap-3 mb-1">
                    <strong className="font-medium text-slate-900">{a.action_type}</strong>
                    <Badge tone={a.status === 'concluded' ? 'success' : 'neutral'}>
                      {a.status}
                    </Badge>
                  </div>
                  <p>{a.description}</p>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      <Card>
        <Card.Header>
          <Card.Title>Evidence</Card.Title>
        </Card.Header>
        <EvidenceUploader evidence={evidence} onUpload={handleUpload} />
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

export default ComplaintDetails;
