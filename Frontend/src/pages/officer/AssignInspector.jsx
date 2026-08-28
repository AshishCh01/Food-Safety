import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { assignInspector, getDistrictComplaint, listInspectors } from '../../services/complaintService';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Alert from '../../components/ui/Alert';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import Textarea from '../../components/ui/Textarea';

function AssignInspector() {
  const { complaintId } = useParams();
  const { getAccessToken } = useAuth();
  const navigate = useNavigate();
  const [complaint, setComplaint] = useState(null);
  const [inspectors, setInspectors] = useState([]);
  const [inspectorStaffId, setInspectorStaffId] = useState('');
  const [dueAt, setDueAt] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([getDistrictComplaint(complaintId, token), listInspectors(token)])
      .then(([complaintData, inspectorList]) => {
        setComplaint(complaintData);
        setInspectors(inspectorList);
      })
      .catch((err) => setError(err.message));
  }, [complaintId, getAccessToken]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await assignInspector(
        complaintId,
        { inspectorStaffId, dueAt: dueAt ? new Date(dueAt).toISOString() : null, notes },
        getAccessToken(),
      );
      navigate(`/officer/complaints/${complaintId}`, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!complaint) {
    return (
      <ContentContainer className="max-w-xl">
        {error ? <ErrorState message={error} /> : <Skeleton.List rows={3} />}
      </ContentContainer>
    );
  }

  return (
    <ContentContainer className="max-w-xl">
      <PageHeader
        title="Assign an inspector"
        description={`${complaint.complaint_number} · ${complaint.title}`}
      />

      {inspectors.length === 0 ? (
        <EmptyState title="No active inspectors are available in your district." />
      ) : (
        <Card as="form" onSubmit={handleSubmit} className="flex flex-col gap-4">
          <FormField label="Inspector" htmlFor="inspector-select" required>
            <Select
              id="inspector-select"
              value={inspectorStaffId}
              onChange={(event) => setInspectorStaffId(event.target.value)}
              required
            >
              <option value="">Select an inspector</option>
              {inspectors.map((inspector) => (
                <option key={inspector.id} value={inspector.id}>
                  {inspector.full_name} ({inspector.employee_code})
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Due date" htmlFor="due-at" hint="Optional">
            <Input id="due-at" type="date" value={dueAt} onChange={(event) => setDueAt(event.target.value)} />
          </FormField>
          <FormField label="Notes" htmlFor="assignment-notes" hint="Optional">
            <Textarea id="assignment-notes" value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
          </FormField>
          {error && <Alert tone="danger">{error}</Alert>}
          <Button type="submit" disabled={!inspectorStaffId} loading={isSubmitting} className="self-start">
            {isSubmitting ? 'Assigning…' : 'Assign inspector'}
          </Button>
        </Card>
      )}
    </ContentContainer>
  );
}

export default AssignInspector;
