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
} from '../../services/complaintService';

function ComplaintDetails() {
  const { complaintId } = useParams();
  const { getAccessToken } = useAuth();
  const location = useLocation();
  const [complaint, setComplaint] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    const token = getAccessToken();
    Promise.all([
      getComplaint(complaintId, token),
      getComplaintTimeline(complaintId, token),
      listEvidence(complaintId, token),
    ])
      .then(([complaintData, timelineData, evidenceData]) => {
        setComplaint(complaintData);
        setTimeline(timelineData);
        setEvidence(evidenceData);
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
          <dd>{complaint.category_name}</dd>
          <dt>Priority</dt>
          <dd>
            <Badge tone={priority.tone}>{priority.label}</Badge>
          </dd>
          <dt>District</dt>
          <dd>{complaint.district_name}</dd>
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
