import { useEffect, useState } from 'react';
import { CheckCircle2, FileText, PlusCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Button from '../../components/ui/Button';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import StatTile from '../../components/ui/StatTile';
import { useAuth } from '../../hooks/useAuth';
import { listMyComplaints } from '../../services/complaintService';

function CitizenDashboard() {
  const { user, getAccessToken } = useAuth();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([
      listMyComplaints(token, { page: 1, pageSize: 1 }),
      listMyComplaints(token, { status: 'resolved', page: 1, pageSize: 1 }),
    ])
      .then(([total, resolved]) => setStats({ total: total.total, resolved: resolved.total }))
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <ContentContainer>
      <PageHeader
        title={`Welcome, ${user?.full_name || ''}`}
        description="Report a food safety issue and track its progress here."
        actions={
          <Link to="/citizen/complaints/new">
            <Button>
              <PlusCircle className="size-4" aria-hidden="true" />
              Report a new issue
            </Button>
          </Link>
        }
      />

      {error && <ErrorState message={error} />}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {!stats && !error ? (
          <>
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </>
        ) : (
          stats && (
            <>
              <StatTile label="Total complaints" value={stats.total} icon={FileText} tone="brand" />
              <StatTile label="Resolved" value={stats.resolved} icon={CheckCircle2} tone="success" />
              <StatTile label="Open" value={Math.max(stats.total - stats.resolved, 0)} icon={FileText} tone="warning" />
            </>
          )
        )}
      </div>

      <Link to="/citizen/complaints" className="text-sm font-medium text-brand-700 hover:underline">
        View all my complaints &rarr;
      </Link>
    </ContentContainer>
  );
}

export default CitizenDashboard;
