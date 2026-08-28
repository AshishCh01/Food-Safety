import Alert from '../ui/Alert';
import Button from '../ui/Button';

/** Shared chrome for every "AI advisory result" panel (Complaint Triage,
 * Evidence Analysis, Investigation Brief): header + run/re-run button,
 * request-level error, empty state, and failed-result state. The completed
 * body (very different per agent) is passed as children, shown only when
 * `status === 'completed'`. */
function AiResultPanel({
  as: Tag = 'section',
  titleAs: Heading = 'h2',
  title,
  hasResult,
  isRunning,
  error,
  status,
  failureMessage,
  emptyMessage,
  onRun,
  runLabel,
  rerunLabel,
  runningLabel,
  children,
}) {
  return (
    <Tag className="rounded-lg border border-brand-200 bg-brand-50/40 p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <Heading className="text-base font-semibold text-slate-900">{title}</Heading>
        <Button type="button" size="sm" variant="secondary" onClick={onRun} disabled={isRunning} loading={isRunning}>
          {isRunning ? runningLabel : hasResult ? rerunLabel : runLabel}
        </Button>
      </div>

      {error && (
        <Alert tone="danger" className="mb-3">
          {error}
        </Alert>
      )}

      {!hasResult && !error && !isRunning && <p className="text-sm text-slate-600">{emptyMessage}</p>}

      {status === 'failed' && (
        <Alert tone="danger" className="mb-3">
          {failureMessage}
        </Alert>
      )}

      {status === 'completed' && <div className="flex flex-col gap-3 text-sm text-slate-700">{children}</div>}
    </Tag>
  );
}

export function UncertainBanner({ children }) {
  return <Alert tone="warning">{children}</Alert>;
}

export function AiMeta({ children }) {
  return <p className="border-t border-brand-200 pt-3 text-xs text-slate-500">{children}</p>;
}

export function AiSection({ title, children }) {
  return (
    <div>
      <h4 className="mb-1 text-sm font-semibold text-slate-800">{title}</h4>
      {children}
    </div>
  );
}

export default AiResultPanel;
