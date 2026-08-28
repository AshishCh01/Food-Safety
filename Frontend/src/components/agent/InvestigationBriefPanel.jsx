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
    <section className="ai-investigation-panel">
      <div className="page-header">
        <h2>AI Investigation Brief (Advisory)</h2>
        <button type="button" onClick={onRun} disabled={isRunning}>
          {isRunning ? 'Running investigation...' : brief ? 'Re-run investigation' : 'Run investigation'}
        </button>
      </div>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {!brief && !error && !isRunning && (
        <p className="ai-investigation-empty">
          No investigation brief yet. Running it synthesizes this complaint's history, evidence, and relevant
          regulations into a summary for your review - it does not change the complaint, assign anyone, or decide
          the outcome.
        </p>
      )}

      {brief && brief.status === 'failed' && (
        <p className="form-error" role="alert">
          The last investigation attempt failed: {brief.error_message || 'Unknown error.'}
        </p>
      )}

      {brief && brief.status === 'completed' && (
        <>
          {brief.is_uncertain && (
            <div className="ai-investigation-uncertain-banner" role="alert">
              <p>AI confidence is low for this brief. Treat it as a starting point only and verify details yourself.</p>
              {brief.uncertainty_reasons.length > 0 && (
                <ul>
                  {brief.uncertainty_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {brief.case_summary && (
            <>
              <h3>Case summary</h3>
              <p>{brief.case_summary}</p>
            </>
          )}

          {brief.risk_indicators.length > 0 && (
            <>
              <h3>Risk indicators</h3>
              <ul>
                {brief.risk_indicators.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          {brief.complaint_patterns.length > 0 && (
            <>
              <h3>Complaint/inspection patterns</h3>
              <ul>
                {brief.complaint_patterns.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          {brief.business_history && (
            <>
              <h3>Business history</h3>
              <dl className="complaint-detail-grid">
                <dt>Previous complaints</dt>
                <dd>{brief.business_history.previous_complaints_count}</dd>
                <dt>Previous inspections</dt>
                <dd>{brief.business_history.previous_inspections_count}</dd>
              </dl>
            </>
          )}

          {brief.relevant_evidence.length > 0 && (
            <>
              <h3>Relevant evidence analysis</h3>
              <ul>
                {brief.relevant_evidence.map((item) => (
                  <li key={item.evidence_id}>
                    {item.file_name}
                    {item.product_name ? ` – ${item.product_name}` : ''}
                    {item.possible_expired === true ? ' (possible expired product)' : ''}
                  </li>
                ))}
              </ul>
            </>
          )}

          {brief.regulatory_guidance.length > 0 && (
            <>
              <h3>Relevant regulatory guidance</h3>
              <ul className="ai-investigation-guidance-list">
                {brief.regulatory_guidance.map((entry, index) => (
                  // eslint-disable-next-line react/no-array-index-key
                  <li key={index}>
                    <p>{entry.guidance}</p>
                    <p className="ai-investigation-citation">
                      Source: {entry.citation.title}
                      {entry.citation.source_organization ? ` (${entry.citation.source_organization})` : ''}
                      {entry.citation.page_number ? `, page ${entry.citation.page_number}` : ''}
                      {entry.citation.section_title ? `, "${entry.citation.section_title}"` : ''}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          )}

          {brief.missing_information.length > 0 && (
            <>
              <h3>Missing information</h3>
              <ul>
                {brief.missing_information.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          {brief.suggested_actions.length > 0 && (
            <>
              <h3>Suggested next steps (not a decision)</h3>
              <ul>
                {brief.suggested_actions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          <p className="ai-investigation-meta">
            Generated by {brief.model_used} on {new Date(brief.created_at).toLocaleString()} &middot; confidence{' '}
            {brief.confidence !== null ? `${Math.round(brief.confidence * 100)}%` : 'unknown'}. This brief is AI-
            generated case intelligence only - it is not an official finding, and it does not decide this
            complaint's outcome.
          </p>
        </>
      )}
    </section>
  );
}

export default InvestigationBriefPanel;
