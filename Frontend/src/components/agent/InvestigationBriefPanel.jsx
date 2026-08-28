import { formatDateTime } from '../../utils/formatters';
import DetailGrid from '../ui/DetailGrid';
import AiResultPanel, { AiMeta, AiSection, UncertainBanner } from './AiResultPanel';

// Displays the AI Investigation Agent's most recent brief for a complaint and
// lets a district officer (re-)run it on demand (Phase 9, see
// docs/AI_AGENTS_ARCHITECTURE.md section 6). This is structured case
// intelligence, not a chatbot: every section below is either a deterministic
// fact pulled straight from the case record (relevant evidence, business
// history) or a clearly-labelled AI-generated analysis (summary, patterns,
// risk indicators, regulatory guidance, suggested actions). Running it never
// changes the complaint, its status, or any official finding - the final
// decision always remains with the officer.
function InvestigationBriefPanel({ brief, isRunning, error, onRun }) {
  return (
    <AiResultPanel
      title="AI Investigation Brief (Advisory)"
      hasResult={Boolean(brief)}
      isRunning={isRunning}
      error={error}
      status={brief?.status}
      failureMessage={`The last investigation attempt failed: ${brief?.error_message || 'Unknown error.'}`}
      emptyMessage="No investigation brief yet. Running it synthesizes this complaint's history, evidence, and relevant regulations into a summary for your review - it does not change the complaint, assign anyone, or decide the outcome."
      onRun={onRun}
      runLabel="Run investigation"
      rerunLabel="Re-run investigation"
      runningLabel="Running investigation…"
    >
      {brief?.is_uncertain && (
        <UncertainBanner>
          <p>AI confidence is low for this brief. Treat it as a starting point only and verify details yourself.</p>
          {brief.uncertainty_reasons.length > 0 && (
            <ul className="mt-1 list-disc space-y-0.5 pl-5">
              {brief.uncertainty_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
        </UncertainBanner>
      )}

      {brief?.case_summary && (
        <AiSection title="Case summary">
          <p>{brief.case_summary}</p>
        </AiSection>
      )}

      {brief?.risk_indicators?.length > 0 && (
        <AiSection title="Risk indicators">
          <ul className="list-disc space-y-0.5 pl-5">
            {brief.risk_indicators.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </AiSection>
      )}

      {brief?.complaint_patterns?.length > 0 && (
        <AiSection title="Complaint/inspection patterns">
          <ul className="list-disc space-y-0.5 pl-5">
            {brief.complaint_patterns.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </AiSection>
      )}

      {brief?.business_history && (
        <AiSection title="Business history">
          <DetailGrid>
            <dt>Previous complaints</dt>
            <dd>{brief.business_history.previous_complaints_count}</dd>
            <dt>Previous inspections</dt>
            <dd>{brief.business_history.previous_inspections_count}</dd>
          </DetailGrid>
        </AiSection>
      )}

      {brief?.relevant_evidence?.length > 0 && (
        <AiSection title="Relevant evidence analysis">
          <ul className="list-disc space-y-0.5 pl-5">
            {brief.relevant_evidence.map((item) => (
              <li key={item.evidence_id}>
                {item.file_name}
                {item.product_name ? ` – ${item.product_name}` : ''}
                {item.possible_expired === true ? ' (possible expired product)' : ''}
              </li>
            ))}
          </ul>
        </AiSection>
      )}

      {brief?.regulatory_guidance?.length > 0 && (
        <AiSection title="Relevant regulatory guidance">
          <ul className="flex flex-col gap-2">
            {brief.regulatory_guidance.map((entry, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={index} className="rounded-md border border-slate-200 bg-white p-2.5">
                <p>{entry.guidance}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Source: {entry.citation.title}
                  {entry.citation.source_organization ? ` (${entry.citation.source_organization})` : ''}
                  {entry.citation.page_number ? `, page ${entry.citation.page_number}` : ''}
                  {entry.citation.section_title ? `, "${entry.citation.section_title}"` : ''}
                </p>
              </li>
            ))}
          </ul>
        </AiSection>
      )}

      {brief?.missing_information?.length > 0 && (
        <AiSection title="Missing information">
          <ul className="list-disc space-y-0.5 pl-5">
            {brief.missing_information.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </AiSection>
      )}

      {brief?.suggested_actions?.length > 0 && (
        <AiSection title="Suggested next steps (not a decision)">
          <ul className="list-disc space-y-0.5 pl-5">
            {brief.suggested_actions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </AiSection>
      )}

      {brief && (
        <AiMeta>
          Generated by {brief.model_used} on {formatDateTime(brief.created_at)} &middot; confidence{' '}
          {brief.confidence !== null && brief.confidence !== undefined ? `${Math.round(brief.confidence * 100)}%` : 'unknown'}.
          This brief is AI-generated case intelligence only - it is not an official finding, and it does not decide
          this complaint&apos;s outcome.
        </AiMeta>
      )}
    </AiResultPanel>
  );
}

export default InvestigationBriefPanel;
