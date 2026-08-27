import { useState } from 'react';

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
      <form onSubmit={handleSubmit} className="status-update-form">
        <label htmlFor="inspection-scheduled-at">
          Scheduled date (optional)
          <input
            id="inspection-scheduled-at"
            type="datetime-local"
            value={scheduledAt}
            onChange={(event) => setScheduledAt(event.target.value)}
          />
        </label>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Scheduling...' : 'Schedule inspection'}
        </button>
      </form>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="status-update-form">
      <label htmlFor="inspection-summary">
        Summary
        <textarea
          id="inspection-summary"
          value={summary}
          onChange={(event) => setSummary(event.target.value)}
          rows={4}
          required
        />
      </label>
      <label htmlFor="inspection-action-recommended">
        Recommended action
        <textarea
          id="inspection-action-recommended"
          value={actionRecommended}
          onChange={(event) => setActionRecommended(event.target.value)}
          rows={2}
          required
        />
      </label>
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Completing...' : 'Complete inspection'}
      </button>
    </form>
  );
}

export default InspectionForm;
