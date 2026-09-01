import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import EvidenceAnalysisPanel from './EvidenceAnalysisPanel';

const EVIDENCE_ITEM = { id: 'ev-1', file_name: 'photo.jpg' };

const COMPLETED_ANALYSIS = {
  id: 'analysis-1',
  evidence_id: 'ev-1',
  status: 'completed',
  model_used: 'gemini-3.7-flash',
  extracted_text: 'Shree Dairy Toned Milk EXP 01/2027',
  product_name: 'Toned Milk',
  manufacturer: 'Shree Dairy',
  batch_lot_number: 'B12345',
  manufacturing_date_text: '01/2026',
  expiry_date_text: '01/2027',
  possible_expired: false,
  packaging_observations: 'Packet is sealed and intact.',
  hygiene_observations: null,
  foreign_object_observations: null,
  uncertainty_notes: [],
  confidence: 0.85,
  is_uncertain: false,
  error_code: null,
  error_message: null,
  created_at: '2026-08-27T12:00:00Z',
};

describe('EvidenceAnalysisPanel', () => {
  it('prompts to analyze when no result exists yet', () => {
    render(
      <EvidenceAnalysisPanel evidenceItem={EVIDENCE_ITEM} analysis={null} isRunning={false} error={null} onRun={() => {}} />
    );

    expect(screen.getByText(/no ai analysis yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze with ai/i })).toBeInTheDocument();
  });

  it('calls onRun when the button is clicked', () => {
    const onRun = vi.fn();
    render(
      <EvidenceAnalysisPanel evidenceItem={EVIDENCE_ITEM} analysis={null} isRunning={false} error={null} onRun={onRun} />
    );

    fireEvent.click(screen.getByRole('button', { name: /analyze with ai/i }));

    expect(onRun).toHaveBeenCalledTimes(1);
  });

  it('disables the button and shows a running state while analysis is in progress', () => {
    render(
      <EvidenceAnalysisPanel evidenceItem={EVIDENCE_ITEM} analysis={null} isRunning error={null} onRun={() => {}} />
    );

    expect(screen.getByRole('button', { name: /analyzing/i })).toBeDisabled();
  });

  it('renders a completed result with extracted text, product details, and dates', () => {
    render(
      <EvidenceAnalysisPanel
        evidenceItem={EVIDENCE_ITEM}
        analysis={COMPLETED_ANALYSIS}
        isRunning={false}
        error={null}
        onRun={() => {}}
      />
    );

    expect(screen.getByText(/shree dairy toned milk exp 01\/2027/i)).toBeInTheDocument();
    expect(screen.getByText('Toned Milk')).toBeInTheDocument();
    expect(screen.getByText('Shree Dairy')).toBeInTheDocument();
    expect(screen.getByText('B12345')).toBeInTheDocument();
    expect(screen.getByText('85%', { exact: false })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /re-analyze/i })).toBeInTheDocument();
  });

  it('shows the possible-expired banner when possible_expired is true', () => {
    const expired = { ...COMPLETED_ANALYSIS, possible_expired: true };
    render(
      <EvidenceAnalysisPanel evidenceItem={EVIDENCE_ITEM} analysis={expired} isRunning={false} error={null} onRun={() => {}} />
    );

    expect(screen.getByRole('alert')).toHaveTextContent(/possible expired product/i);
  });

  it('does not show the possible-expired banner when possible_expired is false or null', () => {
    render(
      <EvidenceAnalysisPanel
        evidenceItem={EVIDENCE_ITEM}
        analysis={COMPLETED_ANALYSIS}
        isRunning={false}
        error={null}
        onRun={() => {}}
      />
    );

    expect(screen.queryByText(/possible expired product/i)).not.toBeInTheDocument();
  });

  it('shows an uncertainty banner when the AI result is flagged uncertain', () => {
    const uncertain = { ...COMPLETED_ANALYSIS, is_uncertain: true };
    render(
      <EvidenceAnalysisPanel evidenceItem={EVIDENCE_ITEM} analysis={uncertain} isRunning={false} error={null} onRun={() => {}} />
    );

    expect(screen.getByRole('alert')).toHaveTextContent(/low/i);
  });

  it('shows the failure message when the last run failed', () => {
    const failed = { ...COMPLETED_ANALYSIS, status: 'failed', error_message: 'The AI service is unavailable.' };
    render(
      <EvidenceAnalysisPanel evidenceItem={EVIDENCE_ITEM} analysis={failed} isRunning={false} error={null} onRun={() => {}} />
    );

    expect(screen.getByText(/the ai service is unavailable/i)).toBeInTheDocument();
  });

  it('shows a request-level error banner separately from a failed AI result', () => {
    render(
      <EvidenceAnalysisPanel
        evidenceItem={EVIDENCE_ITEM}
        analysis={null}
        isRunning={false}
        error="Network error"
        onRun={() => {}}
      />
    );

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });
});
