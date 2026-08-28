import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { listAuditLogs } from '../../services/auditLogService';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import DetailsList from '../../components/ui/DetailsList';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Pagination from '../../components/ui/Pagination';
import Skeleton from '../../components/ui/Skeleton';
import { formatDateTime } from '../../utils/formatters';

const PAGE_SIZE = 20;

function AuditLogs() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    listAuditLogs(getAccessToken(), {
      action: actionFilter || undefined,
      entityType: entityTypeFilter || undefined,
      page,
      pageSize: PAGE_SIZE,
    })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, actionFilter, entityTypeFilter, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <ContentContainer>
      <PageHeader title="Audit Logs" />

      {error && <ErrorState message={error} />}

      <div className="flex flex-wrap gap-3">
        <FormField label="Action" htmlFor="action-filter" className="w-56">
          <Input
            id="action-filter"
            type="text"
            placeholder="e.g. complaint_status_changed"
            value={actionFilter}
            onChange={(event) => {
              setPage(1);
              setActionFilter(event.target.value);
            }}
          />
        </FormField>
        <FormField label="Entity type" htmlFor="entity-type-filter" className="w-56">
          <Input
            id="entity-type-filter"
            type="text"
            placeholder="e.g. complaint"
            value={entityTypeFilter}
            onChange={(event) => {
              setPage(1);
              setEntityTypeFilter(event.target.value);
            }}
          />
        </FormField>
      </div>

      {!result && !error && <Skeleton.List rows={5} />}
      {result && result.items.length === 0 && <EmptyState title="No audit records match these filters." />}

      <ul className="flex flex-col gap-2">
        {result?.items.map((entry) => (
          <li key={entry.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="font-mono text-sm font-medium text-slate-900">{entry.action}</p>
            <p className="mt-0.5 text-xs text-slate-500">
              {entry.actor_name} &middot; {entry.entity_type} {entry.entity_id} &middot; {formatDateTime(entry.created_at)}
            </p>
            {entry.details && <DetailsList data={entry.details} />}
          </li>
        ))}
      </ul>

      {result && result.total > PAGE_SIZE && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />
      )}
    </ContentContainer>
  );
}

export default AuditLogs;
