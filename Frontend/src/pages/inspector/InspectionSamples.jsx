import { useState, useEffect, useCallback } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Badge from '../../components/ui/Badge';
import { useAuth } from '../../hooks/useAuth';
import { listSamplesForInspection, collectSample, dispatchSample } from '../../services/sampleService';
import { listFoodAnalysts } from '../../services/foodAnalystService';

function InspectionSamples({ inspectionId, readOnly = false }) {
  const { getAccessToken } = useAuth();
  const [samples, setSamples] = useState([]);
  const [analysts, setAnalysts] = useState([]);
  const [isCollectModalOpen, setCollectModalOpen] = useState(false);
  const [dispatchSampleId, setDispatchSampleId] = useState(null);
  
  // Forms
  const [collectForm, setCollectForm] = useState({ item_description: '', quantity: '', unit: '', seal_number: '' });
  const [dispatchForm, setDispatchForm] = useState({ analyst_id: '', lab_name: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadSamples = useCallback(async () => {
    try {
      const data = await listSamplesForInspection(inspectionId, getAccessToken());
      setSamples(data);
    } catch (err) {
      console.error(err);
    }
  }, [inspectionId, getAccessToken]);

  const loadAnalysts = useCallback(async () => {
    try {
      const res = await listFoodAnalysts(getAccessToken());
      setAnalysts(res.items || res);
    } catch (err) {
      console.error(err);
    }
  }, [getAccessToken]);

  useEffect(() => {
    if (inspectionId) {
      loadSamples();
      loadAnalysts();
    }
  }, [inspectionId, loadSamples, loadAnalysts]);

  const handleCollect = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await collectSample(inspectionId, collectForm, getAccessToken());
      setCollectModalOpen(false);
      setCollectForm({ item_description: '', quantity: '', unit: '', seal_number: '' });
      loadSamples();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDispatch = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        food_analyst_id: dispatchForm.analyst_id || null,
        lab_name: dispatchForm.lab_name || null,
      };
      await dispatchSample(dispatchSampleId, payload, getAccessToken());
      setDispatchSampleId(null);
      setDispatchForm({ analyst_id: '', lab_name: '' });
      loadSamples();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Samples</Card.Title>
        {!readOnly && (
          <Button size="sm" onClick={() => setCollectModalOpen(true)}>
            Collect Sample
          </Button>
        )}
      </Card.Header>

      <div className="p-4 sm:p-5">
        {samples.length === 0 ? (
          <p className="text-sm text-slate-500">No samples collected yet.</p>
        ) : (
          <Table>
            <Table.Head>
              <Table.Tr>
                <Table.Th>Sample Code</Table.Th>
                <Table.Th>Item</Table.Th>
                <Table.Th>Quantity</Table.Th>
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
                  <Table.Td>
                    <Badge tone={s.status === 'collected' ? 'neutral' : 'success'}>
                      {s.status.replace('_', ' ')}
                    </Badge>
                  </Table.Td>
                  <Table.Td className="text-right">
                    {!readOnly && s.status === 'collected' && (
                      <Button size="sm" variant="secondary" onClick={() => setDispatchSampleId(s.id)}>
                        Dispatch
                      </Button>
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Body>
          </Table>
        )}
      </div>

      <Modal open={isCollectModalOpen} onClose={() => !isSubmitting && setCollectModalOpen(false)} title="Collect Sample">
        <form onSubmit={handleCollect} className="space-y-4">
          <FormField label="Item Description">
            <Input
              required
              value={collectForm.item_description}
              onChange={(e) => setCollectForm((prev) => ({ ...prev, item_description: e.target.value }))}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Quantity">
              <Input
                required
                type="number"
                step="0.01"
                value={collectForm.quantity}
                onChange={(e) => setCollectForm((prev) => ({ ...prev, quantity: e.target.value }))}
              />
            </FormField>
            <FormField label="Unit">
              <Input
                required
                placeholder="e.g. g, ml, packet"
                value={collectForm.unit}
                onChange={(e) => setCollectForm((prev) => ({ ...prev, unit: e.target.value }))}
              />
            </FormField>
          </div>
          <FormField label="Seal Number">
            <Input
              required
              value={collectForm.seal_number}
              onChange={(e) => setCollectForm((prev) => ({ ...prev, seal_number: e.target.value }))}
            />
          </FormField>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setCollectModalOpen(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              Collect
            </Button>
          </div>
        </form>
      </Modal>

      <Modal open={!!dispatchSampleId} onClose={() => !isSubmitting && setDispatchSampleId(null)} title="Dispatch Sample">
        <form onSubmit={handleDispatch} className="space-y-4">
          <FormField label="Assign to Food Analyst">
            <Select
              value={dispatchForm.analyst_id}
              onChange={(e) => {
                setDispatchForm((prev) => ({ ...prev, analyst_id: e.target.value }));
                if (e.target.value) setDispatchForm((prev) => ({ ...prev, lab_name: '' }));
              }}
            >
              <option value="">Select an analyst...</option>
              {analysts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.full_name} ({a.employee_code})
                </option>
              ))}
            </Select>
          </FormField>
          <div className="text-center text-sm text-slate-500 font-medium">OR</div>
          <FormField label="External Lab Name">
            <Input
              value={dispatchForm.lab_name}
              onChange={(e) => {
                setDispatchForm((prev) => ({ ...prev, lab_name: e.target.value }));
                if (e.target.value) setDispatchForm((prev) => ({ ...prev, analyst_id: '' }));
              }}
              placeholder="e.g. State Quality Lab"
            />
          </FormField>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setDispatchSampleId(null)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || (!dispatchForm.analyst_id && !dispatchForm.lab_name)}>
              Dispatch
            </Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
}

export default InspectionSamples;
