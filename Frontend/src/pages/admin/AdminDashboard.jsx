import { useEffect, useState } from 'react';
import { Building2, CheckCircle2, ClipboardList, Clock, FileText, ScrollText, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import CategoryBarChart from '../../components/charts/CategoryBarChart';
import TrendLineChart from '../../components/charts/TrendLineChart';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import ErrorState from '../../components/ui/ErrorState';
import Skeleton from '../../components/ui/Skeleton';
import StatTile from '../../components/ui/StatTile';
import Table from '../../components/ui/Table';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';
import { getAdminAnalytics } from '../../services/analyticsService';

const QUICK_LINKS = [
  { label: 'Staff', path: '/admin/staff', icon: Users },
  { label: 'Businesses', path: '/admin/businesses', icon: Building2 },
  { label: 'Knowledge Base', path: '/admin/rag-documents', icon: FileText },
  { label: 'Audit Logs', path: '/admin/audit-logs', icon: ScrollText },
];

function AdminDashboard() {
  const { getAccessToken } = useAuth();
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([apiRequest('/admin/dashboard', { token }), getAdminAnalytics(token)])
      .then(([dashboardData, analyticsData]) => {
        setStats(dashboardData);
        setAnalytics(analyticsData);
      })
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <ContentContainer>
      <PageHeader title="Admin Dashboard" description="Statewide overview across all districts." />

      {error && <ErrorState message={error} />}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {QUICK_LINKS.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            className="flex flex-col items-center gap-1.5 rounded-lg border border-slate-200 bg-white p-4 text-center text-sm font-medium text-slate-700 hover:border-brand-300 hover:bg-brand-50/30"
          >
            <link.icon className="size-5 text-brand-700" aria-hidden="true" />
            {link.label}
          </Link>
        ))}
        {stats && (
          <div className="col-span-2 flex flex-col items-center justify-center gap-0.5 rounded-lg border border-slate-200 bg-white p-4 text-center sm:col-span-1">
            <span className="text-lg font-semibold text-slate-900">{stats.district_count}</span>
            <span className="text-xs text-slate-500">Districts ({stats.division_count} divisions)</span>
          </div>
        )}
      </div>

      {stats && (
        <Card>
          <Card.Header>
            <Card.Title>Staff and users</Card.Title>
          </Card.Header>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Citizens" value={stats.citizen_count} icon={Users} />
            <StatTile label="District officers" value={stats.district_officer_count} icon={Users} tone="brand" />
            <StatTile label="Inspectors" value={stats.inspector_count} icon={Users} tone="info" />
            <StatTile label="Admins" value={stats.admin_count} icon={Users} tone="warning" />
          </div>
        </Card>
      )}

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
                <Card.Title>Statewide complaint trend</Card.Title>
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
          </div>

          <Card padded={false}>
            <div className="p-4 pb-0 sm:p-5 sm:pb-0">
              <Card.Title>By district</Card.Title>
            </div>
            <div className="p-4 sm:p-5">
              <Table>
                <Table.Head>
                  <tr>
                    <Table.Th>District</Table.Th>
                    <Table.Th>Division</Table.Th>
                    <Table.Th>Total</Table.Th>
                    <Table.Th>Pending</Table.Th>
                    <Table.Th>Active</Table.Th>
                    <Table.Th>Resolved</Table.Th>
                    <Table.Th>Rejected</Table.Th>
                  </tr>
                </Table.Head>
                <Table.Body>
                  {analytics.district_breakdown.map((item) => (
                    <Table.Tr key={item.district_id}>
                      <Table.Td className="font-medium text-slate-900">{item.district_name}</Table.Td>
                      <Table.Td>{item.division_name}</Table.Td>
                      <Table.Td>{item.total_complaints}</Table.Td>
                      <Table.Td>{item.pending_complaints}</Table.Td>
                      <Table.Td>{item.active_complaints}</Table.Td>
                      <Table.Td>{item.resolved_complaints}</Table.Td>
                      <Table.Td>{item.rejected_complaints}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Body>
              </Table>
            </div>
          </Card>
        </>
      )}
    </ContentContainer>
  );
}

export default AdminDashboard;
