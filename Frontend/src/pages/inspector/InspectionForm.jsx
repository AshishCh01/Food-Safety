import { useState } from 'react';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Textarea from '../../components/ui/Textarea';

function InspectionForm({ mode, onSubmit, isSubmitting }) {
  const [scheduledAt, setScheduledAt] = useState('');
  const [summary, setSummary] = useState('');
  const [actionRecommended, setActionRecommended] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    if (mode === 'create') {
      onSubmit({ scheduledAt: scheduledAt ? new Date(scheduledAt).toISOString() : null });
    } else {
      onSubmit({ summary, actionRecommended });
    }
  }

  if (mode === 'create') {
    return (
      <Card as="form" onSubmit={handleSubmit} className="flex flex-col gap-4">
        <FormField label="Scheduled date" htmlFor="inspection-scheduled-at" hint="Optional">
          <Input
            id="inspection-scheduled-at"
            type="datetime-local"
            value={scheduledAt}
            onChange={(event) => setScheduledAt(event.target.value)}
          />
        </FormField>
        <Button type="submit" loading={isSubmitting} className="self-start">
          {isSubmitting ? 'Scheduling…' : 'Schedule inspection'}
        </Button>
      </Card>
    );
  }

  return (
    <Card as="form" onSubmit={handleSubmit} className="flex flex-col gap-4">
      <FormField label="Summary" htmlFor="inspection-summary" required>
        <Textarea
          id="inspection-summary"
          value={summary}
          onChange={(event) => setSummary(event.target.value)}
          rows={4}
          required
        />
      </FormField>
      <FormField label="Recommended action" htmlFor="inspection-action-recommended" required>
        <Textarea
          id="inspection-action-recommended"
          value={actionRecommended}
          onChange={(event) => setActionRecommended(event.target.value)}
          rows={2}
          required
        />
      </FormField>
      <Button type="submit" loading={isSubmitting} className="self-start">
        {isSubmitting ? 'Completing…' : 'Complete inspection'}
      </Button>
    </Card>
  );
}

export default InspectionForm;
