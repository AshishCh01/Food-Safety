import { ShieldCheck } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { dashboardPathForRole } from '../../utils/permissions';
import Button from '../ui/Button';

/** Header for the public/unauthenticated routes (Home, Login, Register).
 * Authenticated app pages use AppShell's Topbar instead. */
function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
          <ShieldCheck className="size-6 text-brand-700" aria-hidden="true" />
          <span className="hidden sm:inline">Maharashtra Food Safety Platform</span>
          <span className="sm:hidden">MFSP</span>
        </Link>
        <nav className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <Link
                to={dashboardPathForRole(user.role)}
                className="text-sm font-medium text-slate-600 hover:text-brand-700"
              >
                Dashboard
              </Link>
              <Button variant="secondary" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-brand-700">
                Log in
              </Link>
              <Button size="sm" onClick={() => navigate('/register')}>
                Register
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Navbar;
