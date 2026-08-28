import { FINDING_SEVERITIES, configFor } from '../../utils/statusConfig';
import Badge from '../ui/Badge';
import EmptyState from '../ui/EmptyState';

function FindingList({ findings }) {
  if (!findings || findings.length === 0) {
    return <EmptyState title="No findings recorded yet." />;
  }

  return (
    <ul className="flex flex-col gap-3">
      {findings.map((finding) => {
        const severity = configFor(FINDING_SEVERITIES, finding.severity);
        return (
          <li key={finding.id} className="rounded-lg border border-slate-200 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-slate-500">{finding.check_code}</span>
              <Badge tone={finding.compliant ? 'success' : 'danger'}>
                {finding.compliant ? 'Compliant' : 'Non-compliant'}
              </Badge>
              <Badge tone={severity.tone}>{severity.label}</Badge>
            </div>
            <p className="mt-1.5 text-sm text-slate-700">{finding.finding}</p>
            {finding.corrective_action && (
              <p className="mt-1 text-sm text-slate-600">
                <strong className="font-medium text-slate-800">Corrective action:</strong> {finding.corrective_action}
              </p>
            )}
            {finding.notes && <p className="mt-1 text-sm text-slate-500">{finding.notes}</p>}
          </li>
        );
      })}
    </ul>
  );
}

export default FindingList;
