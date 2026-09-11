import { useState, useEffect, useCallback } from 'react';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import Table from '../../components/ui/Table';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import FormField from '../../components/ui/FormField';
import Select from '../../components/ui/Select';
import Textarea from '../../components/ui/Textarea';
import { useAuth } from '../../hooks/useAuth';
import { listAnalystSamples, receiveSample, submitResult } from '../../services/foodAnalystService';
import { formatDateTime } from '../../utils/formatters';

function SampleReview() {
  const { getAccessToken } = useAuth();
  const [samples, setSamples] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeSampleId, setActiveSampleId] = useState(null);
  const [form, setForm] = useState({ verdict: '', remarks: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listAnalystSamples(getAccessToken());
      setSamples(data.items || data);
    } catch (err) {
      console.error(err);
    }
  }, [getAccessToken]);

  useEffect(() => {
    load();
  }, [load]);

  const handleReceive = async (sampleId) => {
    setIsSubmitting(true);
    try {
      await receiveSample(sampleId, getAccessToken());
      load();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResultSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await submitResult(activeSampleId, form, getAccessToken());
      setIsModalOpen(false);
      setActiveSampleId(null);
      setForm({ verdict: '', remarks: '' });
      load();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openResultModal = (sampleId) => {
    setActiveSampleId(sampleId);
    setForm({ verdict: '', remarks: '' });
    setIsModalOpen(true);
  };

  return (
    <ContentContainer>
      <PageHeader
        title="Sample Review"
        breadcrumbs={[{ label: 'Dashboard', path: '/food-analyst' }]}
      />
      <Card padded={false}>
        <div className="p-4 sm:p-5">
          {samples.length === 0 ? (
            <p className="text-sm text-slate-500">No samples assigned.</p>
          ) : (
            <Table>
              <Table.Head>
                <Table.Tr>
                  <Table.Th>Sample Code</Table.Th>
                  <Table.Th>Item</Table.Th>
                  <Table.Th>Quantity</Table.Th>
                  <Table.Th>Dispatched At</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th className="text-right">Action</Table.Th>
                </Table.Tr>
              </Table.Head>
              <Table.Body>
                {samples.map((s) => (
                  <Table.Tr key={s.id}>
                    <Table.Td className="font-medium text-slate-900">{s.sample_code}</Table.Td>
                    <Table.Td>{s.item_description}</Table.Td>
                    <Table.Td>
                      {s.quantity} {s.unit}
                    </Table.Td>
                    <Table.Td>{formatDateTime(s.dispatched_at)}</Table.Td>
                    <Table.Td>
                      <Badge tone={s.status === 'result_submitted' ? 'success' : s.status === 'received' ? 'info' : 'neutral'}>
                        {s.status.replace('_', ' ')}
                      </Badge>
                    </Table.Td>
                    <Table.Td className="text-right">
                      {s.status === 'dispatched' && (
                        <Button size="sm" variant="secondary" onClick={() => handleReceive(s.id)} disabled={isSubmitting}>
                          Mark Received
                        </Button>
                      )}
                      {s.status === 'received' && (
                        <Button size="sm" onClick={() => openResultModal(s.id)}>
                          Submit Result
                        </Button>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Body>
            </Table>
          )}
        </div>
      </Card>

      <Modal open={isModalOpen} onClose={() => !isSubmitting && setIsModalOpen(false)} title="Submit Lab Result">
        <form onSubmit={handleResultSubmit} className="space-y-4">
          <FormField label="Verdict">
            <Select required value={form.verdict} onChange={(e) => setForm({ ...form, verdict: e.target.value })}>
              <option value="">Select a verdict...</option>
              <option value="safe">Safe (Compliant)</option>
              <option value="unsafe">Unsafe (Non-Compliant)</option>
              <option value="substandard">Substandard</option>
              <option value="misbranded">Misbranded</option>
            </Select>
          </FormField>
          <FormField label="Remarks">
            <Textarea
              required
              rows={4}
              value={form.remarks}
              onChange={(e) => setForm({ ...form, remarks: e.target.value })}
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
    </ContentContainer>
  );
}

export default SampleReview;
