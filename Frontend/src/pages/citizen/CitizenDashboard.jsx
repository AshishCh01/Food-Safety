import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { listMyComplaints } from '../../services/complaintService';

function CitizenDashboard() {
  const { user, getAccessToken } = useAuth();
  const [total, setTotal] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    listMyComplaints(token, { page: 1, pageSize: 1 })
      .then((result) => setTotal(result.total))
      .catch((err) => setError(err.message));
  }, [getAccessToken]);

  return (
    <section>
      <h1>Citizen Dashboard</h1>
      <p>Welcome, {user?.full_name}.</p>
      {error && <p className="form-error">{error}</p>}
      {total !== null && <p>You have submitted {total} complaint(s).</p>}
      <div className="dashboard-actions">
        <Link to="/citizen/complaints/new">Report a new issue</Link>
        <Link to="/citizen/complaints">View my complaints</Link>
      </div>
    </section>
  );
}

export default CitizenDashboard;
