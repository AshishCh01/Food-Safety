import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';
import { listDistrictComplaints } from '../../services/complaintService';

function OfficerDashboard() {
  const { getAccessToken } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [inspectors, setInspectors] = useState([]);
  const [complaintTotal, setComplaintTotal] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    Promise.all([
      apiRequest('/officer/dashboard', { token }),
      apiRequest('/officer/inspectors', { token }),
      listDistrictComplaints(token, { page: 1, pageSize: 1 }),
    ])
      .then(([dashboardData, inspectorList, complaintResult]) => {
        setDashboard(dashboardData);
        setInspectors(inspectorList);
        setComplaintTotal(complaintResult.total);
      })
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <section>
      <h1>District Officer Dashboard</h1>
      {error && <p className="form-error">{error}</p>}
      {dashboard && (
        <p>
          {dashboard.district_name} ({dashboard.district_code}) - {dashboard.inspector_count} inspector(s)
        </p>
      )}
      {complaintTotal !== null && <p>{complaintTotal} complaint(s) in your district.</p>}
      <div className="dashboard-actions">
        <Link to="/officer/complaints">View complaint queue</Link>
        <Link to="/officer/map">View complaint map</Link>
      </div>
      <h2>Inspectors in your district</h2>
      <ul>
        {inspectors.map((inspector) => (
          <li key={inspector.id}>
            {inspector.full_name} - {inspector.employee_code}
          </li>
        ))}
      </ul>
      <p>Inspector assignment will be available in a later phase.</p>
    </section>
  );
}

export default OfficerDashboard;
