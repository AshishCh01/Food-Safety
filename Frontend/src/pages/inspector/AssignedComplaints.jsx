import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Badge from '../../components/ui/Badge';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Pagination from '../../components/ui/Pagination';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import { useAuth } from '../../hooks/useAuth';
import { formatDate } from '../../utils/formatters';
import { ASSIGNMENT_STATUSES, PRIORITIES, configFor } from '../../utils/statusConfig';
import { listAssignments } from '../../services/inspectionService';

const PAGE_SIZE = 10;

function AssignedComplaints() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('');
  const [sort, setSort] = useState('due_at');
  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQ(q);
      setPage(1);
    }, 300);
    return () => clearTimeout(handler);
  }, [q]);

  useEffect(() => {
    const token = getAccessToken();
    listAssignments(token, { status: status || undefined, sort, q: debouncedQ || undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [getAccessToken, status, sort, debouncedQ, page]);

  return (
    <ContentContainer>
      <PageHeader title="My Assigned Complaints" />

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <FormField label="Search" htmlFor="assignment-search" className="max-w-xs flex-1 min-w-[200px]">
          <Input
            id="assignment-search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Complaint # or title..."
          />
        </FormField>
        <FormField label="Sort by" htmlFor="assignment-sort" className="w-40">
          <Select id="assignment-sort" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            <option value="due_at">Due date</option>
            <option value="priority">Priority</option>
            <option value="assigned_at">Recently assigned</option>
          </Select>
        </FormField>
        <FormField label="Status" htmlFor="assignment-status-filter" className="w-40">
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
      </div>

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={4} />}

      {result && result.items.length === 0 && <EmptyState title="No assignments found." />}

      <div className="flex flex-col gap-3">
        {result?.items.map((assignment) => {
          const assignmentStatus = configFor(ASSIGNMENT_STATUSES, assignment.status);
          const priority = configFor(PRIORITIES, assignment.priority);
          const isOverdue = assignment.due_at && new Date(assignment.due_at) < new Date() && assignment.status !== 'completed';

          return (
            <Link
              key={assignment.id}
              to={`/inspector/assignments/${assignment.id}`}
              className="block rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-brand-300 hover:bg-brand-50/30"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-slate-500">{assignment.complaint_number}</span>
                  <Badge tone={priority.tone}>{priority.label}</Badge>
                </div>
                <Badge tone={assignmentStatus.tone}>{assignmentStatus.label}</Badge>
              </div>
              <h3 className="mt-1.5 font-medium text-slate-900">{assignment.complaint_title}</h3>
              {assignment.business_name && (
                <p className="mt-1 text-xs text-slate-500">{assignment.business_name}</p>
              )}
              {assignment.due_at && (
                <p className={`mt-2 ${isOverdue ? 'text-xs text-danger-600 font-medium' : 'text-xs text-slate-400'}`}>
                  {isOverdue ? 'Overdue: ' : 'Due '}{formatDate(assignment.due_at)}
                </p>
              )}
            </Link>
          );
        })}
      </div>

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default AssignedComplaints;
