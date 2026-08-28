import { useEffect, useState } from 'react';
import { Bot, CheckCircle2, ClipboardList, History } from 'lucide-react';
import { Link } from 'react-router-dom';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import StatTile from '../../components/ui/StatTile';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';

const QUICK_LINKS = [
  { label: 'My assigned complaints', path: '/inspector/assignments', icon: ClipboardList },
  { label: 'Inspection history', path: '/inspector/history', icon: History },
  { label: 'Inspector Assistant', path: '/inspector/assistant', icon: Bot },
];

function InspectorDashboard() {
  const { getAccessToken } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiRequest('/inspector/dashboard', { token: getAccessToken() })
      .then(setData)
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <ContentContainer>
      <PageHeader
        title="Inspector Dashboard"
        description={data ? `${data.district_name} (${data.district_code}) · ${data.inspector_name}` : undefined}
      />

      {error && <ErrorState message={error} />}

      {!data && !error && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatTile label="Assigned" value={data.assigned_count} icon={ClipboardList} tone="info" />
          <StatTile label="In progress" value={data.in_progress_count} icon={ClipboardList} tone="warning" />
          <StatTile label="Completed" value={data.completed_count} icon={CheckCircle2} tone="success" />
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {QUICK_LINKS.map((link) => (
          <Link key={link.path} to={link.path}>
            <Card className="flex items-center gap-3 hover:border-brand-300 hover:bg-brand-50/30">
              <link.icon className="size-5 shrink-0 text-brand-700" aria-hidden="true" />
              <span className="text-sm font-medium text-slate-800">{link.label}</span>
            </Card>
          </Link>
        ))}
      </div>
    </ContentContainer>
  );
}

export default InspectorDashboard;
