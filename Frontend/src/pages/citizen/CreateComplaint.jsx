import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ComplaintForm from '../../components/complaint/ComplaintForm';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import ErrorState from '../../components/ui/ErrorState';
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
    return (
      <ContentContainer>
        <ErrorState message={loadError} />
      </ContentContainer>
    );
  }

  return (
    <ContentContainer className="max-w-3xl">
      <PageHeader title="Report a food safety issue" />
      <ComplaintForm
        categories={categories}
        districts={districts}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
        error={error}
        token={getAccessToken()}
      />
      <Card>
        <Card.Header>
          <Card.Title>Attach evidence</Card.Title>
        </Card.Header>
        <p className="mb-2 text-sm text-slate-500">Optional &mdash; photos, videos, or PDFs, uploaded after submission.</p>
        <label className="flex cursor-pointer items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-4 text-sm font-medium text-slate-600 hover:border-brand-400 hover:bg-brand-50/40">
          Choose files
          <input type="file" multiple onChange={handleFileSelection} className="sr-only" />
        </label>
        {evidenceFiles.length > 0 && (
          <ul className="mt-3 flex flex-col gap-1.5">
            {evidenceFiles.map((file) => (
              <li key={file.name} className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700">
                {file.name}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </ContentContainer>
  );
}

export default CreateComplaint;
