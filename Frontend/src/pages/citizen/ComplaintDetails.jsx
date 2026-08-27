import { useCallback, useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import ComplaintStatus from '../../components/complaint/ComplaintStatus';
import ComplaintTimeline from '../../components/complaint/ComplaintTimeline';
import EvidenceUploader from '../../components/complaint/EvidenceUploader';
import LocationMap from '../../components/map/LocationMap';
import { useAuth } from '../../hooks/useAuth';
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
    return <p className="form-error">{error}</p>;
  }

  if (!complaint) {
    return <p>Loading...</p>;
  }

  return (
    <section>
      <div className="page-header">
        <h1>{complaint.title}</h1>
        <ComplaintStatus status={complaint.status} />
      </div>
      <p className="complaint-number">{complaint.complaint_number}</p>

      {location.state?.evidenceWarning && (
        <p className="form-error">Some evidence failed to upload: {location.state.evidenceWarning}</p>
      )}

      <dl className="complaint-detail-grid">
        <dt>Category</dt>
        <dd>{complaint.category_name}</dd>
        <dt>Priority</dt>
        <dd>{complaint.priority}</dd>
        <dt>District</dt>
        <dd>{complaint.district_name}</dd>
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
      <EvidenceUploader evidence={evidence} onUpload={handleUpload} />

      <h2>Timeline</h2>
      <ComplaintTimeline entries={timeline} />
    </section>
  );
}

export default ComplaintDetails;
