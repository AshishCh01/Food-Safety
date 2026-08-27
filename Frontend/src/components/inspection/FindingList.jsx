function FindingList({ findings }) {
  if (!findings || findings.length === 0) {
    return <p>No findings recorded yet.</p>;
  }

  return (
    <ul className="finding-list">
      {findings.map((finding) => (
        <li key={finding.id} className="finding-list-item">
          <div className="finding-list-header">
            <span className="finding-check-code">{finding.check_code}</span>
            <span className={`compliance-tag ${finding.compliant ? 'compliant' : 'non-compliant'}`}>
              {finding.compliant ? 'Compliant' : 'Non-compliant'}
            </span>
            <span className={`priority-tag priority-${finding.severity}`}>{finding.severity}</span>
          </div>
          <p>{finding.finding}</p>
          {finding.corrective_action && (
            <p className="finding-corrective-action">
              <strong>Corrective action:</strong> {finding.corrective_action}
            </p>
          )}
          {finding.notes && <p className="finding-notes">{finding.notes}</p>}
        </li>
      ))}
    </ul>
  );
}

export default FindingList;
