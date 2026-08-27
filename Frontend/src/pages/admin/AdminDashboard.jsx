import { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';

function AdminDashboard() {
  const { getAccessToken } = useAuth();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiRequest('/admin/dashboard', { token: getAccessToken() })
      .then(setStats)
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <section>
      <h1>Admin Dashboard</h1>
      {error && <p className="form-error">{error}</p>}
      {stats && (
        <ul>
          <li>Divisions: {stats.division_count}</li>
          <li>Districts: {stats.district_count}</li>
          <li>Citizens: {stats.citizen_count}</li>
          <li>District officers: {stats.district_officer_count}</li>
          <li>Inspectors: {stats.inspector_count}</li>
          <li>Admins: {stats.admin_count}</li>
        </ul>
      )}
      <p>Staff/user management and audit logs will be available in a later phase.</p>
    </section>
  );
}

export default AdminDashboard;
