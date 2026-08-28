import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import InvestigationBriefPanel from './InvestigationBriefPanel';

const COMPLETED_BRIEF = {
  id: 'brief-1',
  complaint_id: 'complaint-1',
  status: 'completed',
  model_used: 'gemini-3.1-pro',
  case_summary: 'Citizen reports expired milk being sold at Shree Dairy.',
  relevant_evidence: [{ evidence_id: 'ev-1', file_name: 'label.jpg', product_name: 'Toned Milk', possible_expired: true }],
  business_history: { previous_complaints_count: 2, previous_inspections_count: 1 },
  complaint_patterns: ['Two prior expired-food complaints against this business.'],
  regulatory_guidance: [
    {
      guidance: 'Food products must not be sold beyond their expiry date.',
      citation: {
        document_id: 'doc-1',
        title: 'FSSAI Food Safety and Standards Regulations',
        source_organization: 'FSSAI',
        page_number: 42,
        section_title: 'Sale of expired products',
      },
    },
  ],
  risk_indicators: ['Repeat complaints in the same category.'],
  missing_information: ['No inspection has been recorded for this complaint yet.'],
  suggested_actions: ['Verify current license status before scheduling a visit.'],
  confidence: 0.78,
  is_uncertain: false,
  uncertainty_reasons: [],
  error_code: null,
  error_message: null,
  created_at: '2026-08-27T12:00:00Z',
};

describe('InvestigationBriefPanel', () => {
  it('prompts the officer to run an investigation when none exists yet', () => {
    render(<InvestigationBriefPanel brief={null} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByText(/no investigation brief yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^run investigation$/i })).toBeInTheDocument();
  });

  it('calls onRun when the button is clicked', () => {
    const onRun = vi.fn();
    render(<InvestigationBriefPanel brief={null} isRunning={false} error={null} onRun={onRun} />);

    fireEvent.click(screen.getByRole('button', { name: /^run investigation$/i }));

    expect(onRun).toHaveBeenCalledTimes(1);
  });

  it('disables the button and shows a running state while the investigation is in progress', () => {
    render(<InvestigationBriefPanel brief={null} isRunning error={null} onRun={() => {}} />);

    expect(screen.getByRole('button', { name: /running investigation/i })).toBeDisabled();
  });

  it('renders a completed brief with summary, risk indicators, citations, and suggested actions', () => {
    render(<InvestigationBriefPanel brief={COMPLETED_BRIEF} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByText(/citizen reports expired milk/i)).toBeInTheDocument();
    expect(screen.getByText(/repeat complaints in the same category/i)).toBeInTheDocument();
    expect(screen.getByText(/food products must not be sold beyond their expiry date/i)).toBeInTheDocument();
    expect(screen.getByText(/FSSAI Food Safety and Standards Regulations/)).toBeInTheDocument();
    expect(screen.getByText(/verify current license status/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /re-run investigation/i })).toBeInTheDocument();
  });

  it('never renders anything resembling an officer decision or status change control', () => {
    render(<InvestigationBriefPanel brief={COMPLETED_BRIEF} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.queryByRole('button', { name: /verify|reject|resolve|approve/i })).not.toBeInTheDocument();
  });

  it('shows an uncertainty banner with reasons when the brief is flagged uncertain', () => {
    const uncertain = {
      ...COMPLETED_BRIEF,
      is_uncertain: true,
      uncertainty_reasons: ['No matching authoritative regulations were found.'],
    };
    render(<InvestigationBriefPanel brief={uncertain} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByRole('alert')).toHaveTextContent(/low/i);
    expect(screen.getByText(/no matching authoritative regulations were found/i)).toBeInTheDocument();
  });

  it('shows the failure message when the last run failed', () => {
    const failed = { ...COMPLETED_BRIEF, status: 'failed', error_message: 'The AI service is unavailable.' };
    render(<InvestigationBriefPanel brief={failed} isRunning={false} error={null} onRun={() => {}} />);

    expect(screen.getByText(/the ai service is unavailable/i)).toBeInTheDocument();
  });

  it('shows a request-level error banner separately from a failed AI result', () => {
    render(<InvestigationBriefPanel brief={null} isRunning={false} error="Network error" onRun={() => {}} />);

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });
});
