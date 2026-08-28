import { useEffect, useState } from 'react';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Badge from '../../components/ui/Badge';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import Pagination from '../../components/ui/Pagination';
import Skeleton from '../../components/ui/Skeleton';
import { useAuth } from '../../hooks/useAuth';
import { formatDate } from '../../utils/formatters';
import { INSPECTION_STATUSES, configFor } from '../../utils/statusConfig';
import { listInspectionHistory } from '../../services/inspectionService';

const PAGE_SIZE = 10;

function InspectionHistory() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    listInspectionHistory(getAccessToken(), { page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, page]);

  return (
    <ContentContainer>
      <PageHeader title="Inspection History" />

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={4} />}

      {result && result.items.length === 0 && <EmptyState title="No completed inspections yet." />}

      <div className="flex flex-col gap-3">
        {result?.items.map((inspection) => {
          const status = configFor(INSPECTION_STATUSES, inspection.inspection_status);
          return (
            <div key={inspection.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-slate-500">{inspection.complaint_number}</span>
                <Badge tone={status.tone}>{status.label}</Badge>
              </div>
              <div className="mt-1.5 flex flex-wrap gap-3 text-xs text-slate-500">
                {inspection.scheduled_at && <span>Scheduled {formatDate(inspection.scheduled_at)}</span>}
                {inspection.completed_at && <span>Completed {formatDate(inspection.completed_at)}</span>}
              </div>
            </div>
          );
        })}
      </div>

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default InspectionHistory;
