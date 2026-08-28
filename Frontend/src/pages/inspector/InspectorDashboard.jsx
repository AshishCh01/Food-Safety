import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { apiRequest } from '../../services/api';

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
    <section>
      <h1>Inspector Dashboard</h1>
      {error && <p className="form-error">{error}</p>}
      {data && (
        <ul>
          <li>
            District: {data.district_name} ({data.district_code})
          </li>
          <li>Inspector: {data.inspector_name}</li>
          <li>Employee code: {data.employee_code}</li>
          <li>Assigned: {data.assigned_count}</li>
          <li>In progress: {data.in_progress_count}</li>
          <li>Completed: {data.completed_count}</li>
        </ul>
      )}
      <div className="dashboard-actions">
        <Link to="/inspector/assignments">My assigned complaints</Link>
        <Link to="/inspector/history">Inspection history</Link>
        <Link to="/inspector/assistant">Inspector Assistant</Link>
      </div>
    </section>
  );
}

export default InspectorDashboard;
