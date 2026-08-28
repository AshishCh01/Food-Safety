import { useEffect, useState } from 'react';
import { CheckCircle2, ClipboardList, Clock, Map } from 'lucide-react';
import { Link } from 'react-router-dom';
import CategoryBarChart from '../../components/charts/CategoryBarChart';
import TrendLineChart from '../../components/charts/TrendLineChart';
import WorkloadBarChart from '../../components/charts/WorkloadBarChart';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import StatTile from '../../components/ui/StatTile';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';
import { getOfficerAnalytics } from '../../services/analyticsService';
import { PRIORITY_COLORS, configFor, PRIORITIES } from '../../utils/statusConfig';

function OfficerDashboard() {
  const { getAccessToken } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [inspectors, setInspectors] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([
      apiRequest('/officer/dashboard', { token }),
      apiRequest('/officer/inspectors', { token }),
      getOfficerAnalytics(token),
    ])
      .then(([dashboardData, inspectorList, analyticsData]) => {
        setDashboard(dashboardData);
        setInspectors(inspectorList);
        setAnalytics(analyticsData);
      })
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <ContentContainer>
      <PageHeader
        title="District Officer Dashboard"
        description={dashboard ? `${dashboard.district_name} (${dashboard.district_code})` : undefined}
        actions={
          <Link to="/officer/map">
            <Button variant="secondary">
              <Map className="size-4" aria-hidden="true" />
              View complaint map
            </Button>
          </Link>
        }
      />

      {error && <ErrorState message={error} />}

      {!analytics && !error && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      )}

      {analytics && (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Total complaints" value={analytics.total_complaints} icon={ClipboardList} tone="brand" />
            <StatTile label="Pending" value={analytics.pending_complaints} icon={Clock} tone="warning" />
            <StatTile label="Active" value={analytics.active_complaints} icon={ClipboardList} tone="info" />
            <StatTile label="Resolved" value={analytics.resolved_complaints} icon={CheckCircle2} tone="success" />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <Card.Header>
                <Card.Title>Complaint trend</Card.Title>
              </Card.Header>
              <TrendLineChart data={analytics.complaint_trend} />
            </Card>
            <Card>
              <Card.Header>
                <Card.Title>Complaints by category</Card.Title>
              </Card.Header>
              <CategoryBarChart
                data={analytics.category_breakdown.map((item) => ({ label: item.category_name, count: item.count }))}
              />
            </Card>
            <Card>
              <Card.Header>
                <Card.Title>Priority distribution</Card.Title>
              </Card.Header>
              <CategoryBarChart
                data={analytics.priority_breakdown.map((item) => ({
                  label: configFor(PRIORITIES, item.priority).label,
                  count: item.count,
                  color: PRIORITY_COLORS[item.priority],
                }))}
              />
            </Card>
            <Card>
              <Card.Header>
                <Card.Title>Inspector workload</Card.Title>
              </Card.Header>
              <WorkloadBarChart data={analytics.inspector_workload} />
            </Card>
          </div>

          <Card>
            <Card.Header>
              <Card.Title>Inspections</Card.Title>
            </Card.Header>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <StatTile label="Total" value={analytics.inspection_outcomes.total_inspections} />
              <StatTile label="Scheduled" value={analytics.inspection_outcomes.scheduled} />
              <StatTile label="In progress" value={analytics.inspection_outcomes.in_progress} />
              <StatTile label="Completed" value={analytics.inspection_outcomes.completed} />
              <StatTile label="Compliant" value={analytics.inspection_outcomes.compliant_findings} tone="success" />
              <StatTile label="Non-compliant" value={analytics.inspection_outcomes.non_compliant_findings} tone="danger" />
            </div>
          </Card>
        </>
      )}

      <Card>
        <Card.Header>
          <Card.Title>Inspectors in your district</Card.Title>
        </Card.Header>
        {inspectors.length === 0 ? (
          <p className="text-sm text-slate-500">No inspectors in this district yet.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {inspectors.map((inspector) => (
              <li key={inspector.id} className="flex items-center justify-between text-sm text-slate-700">
                <span>{inspector.full_name}</span>
                <span className="font-mono text-xs text-slate-500">{inspector.employee_code}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </ContentContainer>
  );
}

export default OfficerDashboard;
