import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ComplaintForm from '../../components/complaint/ComplaintForm';
import { useAuth } from '../../hooks/useAuth';
import {
  createComplaint,
  listComplaintCategories,
  listDistricts,
  uploadEvidence,
} from '../../services/complaintService';

function CreateComplaint() {
  const { getAccessToken } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [evidenceFiles, setEvidenceFiles] = useState([]);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([listComplaintCategories(token), listDistricts(token)])
      .then(([categoryList, districtList]) => {
        setCategories(categoryList);
        setDistricts(districtList);
      })
      .catch((err) => setLoadError(err.message));
  }, [getAccessToken]);

  function handleFileSelection(event) {
    setEvidenceFiles(Array.from(event.target.files || []));
  }

  async function handleSubmit(payload) {
    setError(null);
    setIsSubmitting(true);
    const token = getAccessToken();
    try {
      const complaint = await createComplaint(payload, token);

      const uploadErrors = [];
      for (const file of evidenceFiles) {
        try {
          // eslint-disable-next-line no-await-in-loop
          await uploadEvidence(complaint.id, file, token);
        } catch (uploadErr) {
          uploadErrors.push(`${file.name}: ${uploadErr.message}`);
        }
      }

      navigate(`/citizen/complaints/${complaint.id}`, {
        replace: true,
        state: uploadErrors.length > 0 ? { evidenceWarning: uploadErrors.join('; ') } : undefined,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loadError) {
    return <p className="form-error">{loadError}</p>;
  }

  return (
    <section>
      <h1>Report a food safety issue</h1>
      <ComplaintForm
        categories={categories}
        districts={districts}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
        error={error}
        token={getAccessToken()}
      />
      <div className="evidence-uploader">
        <label className="evidence-upload-label">
          Attach evidence (optional, uploaded after submission)
          <input type="file" multiple onChange={handleFileSelection} />
        </label>
        {evidenceFiles.length > 0 && (
          <ul className="evidence-list">
            {evidenceFiles.map((file) => (
              <li key={file.name} className="evidence-list-item">
                {file.name}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

export default CreateComplaint;
