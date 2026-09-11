import { useState, useEffect, useCallback } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Textarea from '../../components/ui/Textarea';
import Badge from '../../components/ui/Badge';
import { useAuth } from '../../hooks/useAuth';
import { listLegalActions, createLegalAction, updateLegalAction } from '../../services/legalActionService';
import { formatDateTime } from '../../utils/formatters';
import { formatStatusLabel } from '../../utils/complaintStatus';

function ComplaintLegalActions({ complaintId }) {
  const { getAccessToken } = useAuth();
  const [actions, setActions] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState({ action_type: '', description: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listLegalActions(complaintId, getAccessToken());
      setActions(data);
    } catch (err) {
      console.error(err);
    }
  }, [complaintId, getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await createLegalAction(complaintId, form, getAccessToken());
      setIsModalOpen(false);
      setForm({ action_type: '', description: '' });
      load();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConclude = async (actionId) => {
    setIsSubmitting(true);
    try {
      await updateLegalAction(actionId, { status: 'concluded' }, getAccessToken());
      load();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Legal Actions</Card.Title>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          Add Legal Action
        </Button>
      </Card.Header>
      
      <div className="p-4 sm:p-5 flex flex-col gap-4">
        {actions.length === 0 ? (
          <p className="text-sm text-slate-500">No legal actions recorded.</p>
        ) : (
          actions.map((action) => (
            <div key={action.id} className="rounded-md border border-slate-200 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h4 className="font-semibold text-slate-900">{action.action_type}</h4>
                  <p className="text-sm text-slate-500">{formatDateTime(action.initiated_at)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge tone={action.status === 'concluded' ? 'success' : 'neutral'}>
                    {formatStatusLabel(action.status)}
                  </Badge>
                  {action.status !== 'concluded' && (
                    <Button size="sm" variant="secondary" onClick={() => handleConclude(action.id)} disabled={isSubmitting}>
                      Conclude
                    </Button>
                  )}
                </div>
              </div>
              <p className="mt-2 text-sm text-slate-700">{action.description}</p>
              {action.concluded_at && (
                <p className="mt-2 text-xs text-slate-500">Concluded at: {formatDateTime(action.concluded_at)}</p>
              )}
            </div>
          ))
        )}
      </div>

      <Modal open={isModalOpen} onClose={() => !isSubmitting && setIsModalOpen(false)} title="New Legal Action">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Action Type">
            <Input
              required
              value={form.action_type}
              onChange={(e) => setForm({ ...form, action_type: e.target.value })}
              placeholder="e.g. Fine, Suspension Notice, Court Case"
            />
          </FormField>
          <FormField label="Description">
            <Textarea
              required
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </FormField>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Submit
            </Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
}

export default ComplaintLegalActions;
