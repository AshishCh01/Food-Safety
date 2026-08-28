import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Badge from '../../components/ui/Badge';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Pagination from '../../components/ui/Pagination';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import { useAuth } from '../../hooks/useAuth';
import { formatDate } from '../../utils/formatters';
import { ASSIGNMENT_STATUSES, configFor } from '../../utils/statusConfig';
import { listAssignments } from '../../services/inspectionService';

const PAGE_SIZE = 10;

function AssignedComplaints() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    listAssignments(token, { status: status || undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, status, page]);

  return (
    <ContentContainer>
      <PageHeader title="My Assigned Complaints" />

      <FormField label="Status" htmlFor="assignment-status-filter" className="max-w-xs">
        <Select
          id="assignment-status-filter"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All</option>
          {ASSIGNMENT_STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>
      </FormField>

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={4} />}

      {result && result.items.length === 0 && <EmptyState title="No assignments found." />}

      <div className="flex flex-col gap-3">
        {result?.items.map((assignment) => {
          const assignmentStatus = configFor(ASSIGNMENT_STATUSES, assignment.status);
          return (
            <Link
              key={assignment.id}
              to={`/inspector/assignments/${assignment.id}`}
              className="block rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-brand-300 hover:bg-brand-50/30"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-slate-500">{assignment.complaint_number}</span>
                <Badge tone={assignmentStatus.tone}>{assignmentStatus.label}</Badge>
              </div>
              <h3 className="mt-1.5 font-medium text-slate-900">{assignment.complaint_title}</h3>
              {assignment.due_at && <p className="mt-2 text-xs text-slate-400">Due {formatDate(assignment.due_at)}</p>}
            </Link>
          );
        })}
      </div>

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default AssignedComplaints;
