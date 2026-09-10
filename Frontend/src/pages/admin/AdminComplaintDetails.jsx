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
        <DetailGrid>
          <dt>Title</dt>
          <dd>{complaint.title}</dd>
          
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
          
          <dt>Date submitted</dt>
          <dd>{formatDateTime(complaint.created_at)}</dd>
          
          <dt>Business</dt>
          <dd>{complaint.business?.business_name || 'N/A'}</dd>
          
          <dt>Location</dt>
          <dd>
            {complaint.address_line || complaint.business?.address || 'N/A'}
            <br />
            {complaint.district_name} District
          </dd>
          
          {complaint.business?.business_type && (
            <>
              <dt>Concern</dt>
              <dd>{complaint.business.business_type}</dd>
            </>
          )}
          
          <dt className="sm:col-span-2">Description</dt>
          <dd className="sm:col-span-2">
            <p className="whitespace-pre-wrap">{complaint.description}</p>
          </dd>
        </DetailGrid>
      </Card>
    </ContentContainer>
  );
}

export default AdminComplaintDetails;
