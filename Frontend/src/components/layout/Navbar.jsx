import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { dashboardPathForRole } from '../../utils/permissions';

function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        Maharashtra Food Safety Platform
      </Link>
      <div className="navbar-links">
        {isAuthenticated ? (
          <>
            <Link to={dashboardPathForRole(user.role)}>Dashboard</Link>
            <span className="navbar-user">
              {user.full_name} ({user.role})
            </span>
            <button type="button" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Log in</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
