import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import DetailGrid from '../../components/ui/DetailGrid';
import Badge from '../../components/ui/Badge';
import { useAuth } from '../../hooks/useAuth';
import { getAdminComplaint } from '../../services/complaintService';
import { formatDateTime } from '../../utils/formatters';
import { PRIORITIES, configFor } from '../../utils/statusConfig';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';

function AdminComplaintDetails() {
  const { complaintId } = useParams();
  const { getAccessToken } = useAuth();
  const [complaint, setComplaint] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    getAdminComplaint(complaintId, token)
      .then(setComplaint)
      .catch((err) => setError(err.message));
  }, [complaintId, getAccessToken]);

  if (error) {
    return (
      <ContentContainer>
        <PageHeader title="Complaint details" backTo="/admin/complaints" />
        <ErrorState message={error} />
      </ContentContainer>
    );
  }

  if (!complaint) {
    return (
      <ContentContainer>
        <PageHeader title="Complaint details" backTo="/admin/complaints" />
        <Skeleton.List rows={5} />
      </ContentContainer>
    );
  }

  const priority = configFor(PRIORITIES, complaint.priority);

  return (
    <ContentContainer>
      <PageHeader title={`Complaint ${complaint.complaint_number}`} backTo="/admin/complaints">
        <ComplaintStatus status={complaint.status} />
      </PageHeader>

      <Card>
        <Card.Header>
          <Card.Title>Complaint details</Card.Title>
        </Card.Header>
        <Card.Body>
          <DetailGrid>
            <DetailGrid.Item label="Title">{complaint.title}</DetailGrid.Item>
            <DetailGrid.Item label="Category">{complaint.category_name}</DetailGrid.Item>
            <DetailGrid.Item label="Priority">
              <Badge tone={priority.tone}>{priority.label}</Badge>
            </DetailGrid.Item>
            <DetailGrid.Item label="Date submitted">{formatDateTime(complaint.created_at)}</DetailGrid.Item>
            <DetailGrid.Item label="Business">{complaint.business_name}</DetailGrid.Item>
            <DetailGrid.Item label="Location">
              {complaint.business_address}
              <br />
              {complaint.district_name} District
            </DetailGrid.Item>
            <DetailGrid.Item label="Description" fullWidth>
              <p className="whitespace-pre-wrap">{complaint.description}</p>
            </DetailGrid.Item>
          </DetailGrid>
        </Card.Body>
      </Card>
    </ContentContainer>
  );
}

export default AdminComplaintDetails;
