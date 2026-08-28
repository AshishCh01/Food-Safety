import { useState } from 'react';
import { FINDING_SEVERITIES } from '../../utils/statusConfig';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Checkbox from '../ui/Checkbox';
import FormField from '../ui/FormField';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';

const INITIAL_FORM = {
  checkCode: '',
  finding: '',
  severity: 'medium',
  compliant: true,
  notes: '',
  correctiveAction: '',
};

function FindingForm({ onSubmit, isSubmitting }) {
  const [form, setForm] = useState(INITIAL_FORM);

  function updateField(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
    setForm(INITIAL_FORM);
  }

  return (
    <Card as="form" onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Check code" htmlFor="finding-check-code" required>
          <Input id="finding-check-code" value={form.checkCode} onChange={updateField('checkCode')} required />
        </FormField>
        <FormField label="Severity" htmlFor="finding-severity">
          <Select id="finding-severity" value={form.severity} onChange={updateField('severity')}>
            {FINDING_SEVERITIES.map((severity) => (
              <option key={severity.value} value={severity.value}>
                {severity.label}
              </option>
            ))}
          </Select>
        </FormField>
      </div>
      <FormField label="Finding" htmlFor="finding-text" required>
        <Textarea id="finding-text" value={form.finding} onChange={updateField('finding')} rows={3} required />
      </FormField>
      <Checkbox
        id="finding-compliant"
        label="Compliant"
        checked={form.compliant}
        onChange={(event) => setForm((prev) => ({ ...prev, compliant: event.target.checked }))}
      />
      <FormField label="Notes" htmlFor="finding-notes" hint="Optional">
        <Textarea id="finding-notes" value={form.notes} onChange={updateField('notes')} rows={2} />
      </FormField>
      <FormField label="Corrective action" htmlFor="finding-corrective-action" hint="Optional">
        <Textarea
          id="finding-corrective-action"
          value={form.correctiveAction}
          onChange={updateField('correctiveAction')}
          rows={2}
        />
      </FormField>
      <Button type="submit" loading={isSubmitting} className="self-start">
        {isSubmitting ? 'Adding…' : 'Add finding'}
      </Button>
    </Card>
  );
}

export default FindingForm;
