import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ComplaintTriagePanel from './ComplaintTriagePanel';

const COMPLETED_TRIAGE = {
  id: 'triage-1',
  status: 'completed',
  model_used: 'gemini-3.7-flash',
  suggested_category_id: 'cat-1',
  suggested_category_name: 'Expired Food',
  suggested_category_raw: 'expired_food',
  category_match_uncertain: false,
  suggested_priority: 'high',
  summary: 'Citizen reports expired milk on sale.',
  entities: { business_name: 'Shree Dairy', product: 'milk' },
  missing_information: ['purchase date'],
  confidence: 0.82,
  is_uncertain: false,
  error_code: null,
  error_message: null,
  created_at: '2026-08-27T12:00:00Z',
};

describe('ComplaintTriagePanel', () => {
  it('prompts the officer to run triage when none exists yet', () => {
    render(<ComplaintTriagePanel triage={null} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByText(/no ai analysis yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run ai triage/i })).toBeInTheDocument();
  });

  it('calls onRun when the button is clicked', () => {
    const onRun = vi.fn();
    render(<ComplaintTriagePanel triage={null} isRunning={false} error={null} onRun={onRun} />);

    fireEvent.click(screen.getByRole('button', { name: /run ai triage/i }));

    expect(onRun).toHaveBeenCalledTimes(1);
  });

  it('disables the button and shows a running state while triage is in progress', () => {
    render(<ComplaintTriagePanel triage={null} isRunning error={null} onRun={() => {}} />);

    expect(screen.getByRole('button', { name: /running ai triage/i })).toBeDisabled();
  });

  it('renders a completed result with category, priority, summary, and entities', () => {
    render(<ComplaintTriagePanel triage={COMPLETED_TRIAGE} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByText('Expired Food')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText(/citizen reports expired milk/i)).toBeInTheDocument();
    expect(screen.getByText('Shree Dairy')).toBeInTheDocument();
    expect(screen.getByText('milk')).toBeInTheDocument();
    expect(screen.getByText('purchase date')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /re-run ai triage/i })).toBeInTheDocument();
  });

  it('shows an uncertainty banner when the AI result is flagged uncertain', () => {
    const uncertain = { ...COMPLETED_TRIAGE, is_uncertain: true, category_match_uncertain: true };
    render(<ComplaintTriagePanel triage={uncertain} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByRole('alert')).toHaveTextContent(/low/i);
  });

  it('shows the failure message when the last run failed', () => {
    const failed = { ...COMPLETED_TRIAGE, status: 'failed', error_message: 'The AI service is unavailable.' };
    render(<ComplaintTriagePanel triage={failed} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByText(/the ai service is unavailable/i)).toBeInTheDocument();
  });

  it('shows a request-level error banner separately from a failed AI result', () => {
    render(<ComplaintTriagePanel triage={null} isRunning={false} error="Network error" onRun={() => {}} />);

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });
});
