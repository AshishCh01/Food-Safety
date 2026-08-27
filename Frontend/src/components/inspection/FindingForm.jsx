import { useState } from 'react';

const SEVERITIES = ['low', 'medium', 'high', 'critical'];

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
    <form onSubmit={handleSubmit} className="status-update-form">
      <label htmlFor="finding-check-code">
        Check code
        <input id="finding-check-code" value={form.checkCode} onChange={updateField('checkCode')} required />
      </label>
      <label htmlFor="finding-text">
        Finding
        <textarea id="finding-text" value={form.finding} onChange={updateField('finding')} rows={3} required />
      </label>
      <label htmlFor="finding-severity">
        Severity
        <select id="finding-severity" value={form.severity} onChange={updateField('severity')}>
          {SEVERITIES.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </label>
      <label className="checkbox-label" htmlFor="finding-compliant">
        <input
          id="finding-compliant"
          type="checkbox"
          checked={form.compliant}
          onChange={(event) => setForm((prev) => ({ ...prev, compliant: event.target.checked }))}
        />
        Compliant
      </label>
      <label htmlFor="finding-notes">
        Notes (optional)
        <textarea id="finding-notes" value={form.notes} onChange={updateField('notes')} rows={2} />
      </label>
      <label htmlFor="finding-corrective-action">
        Corrective action (optional)
        <textarea
          id="finding-corrective-action"
          value={form.correctiveAction}
          onChange={updateField('correctiveAction')}
          rows={2}
        />
      </label>
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Adding...' : 'Add finding'}
      </button>
    </form>
  );
}

export default FindingForm;
