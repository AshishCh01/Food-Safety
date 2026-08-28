import { useEffect, useState } from 'react';
import { Bell, LogOut, Menu } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getUnreadNotificationCount } from '../../services/notificationService';
import { formatEnumLabel } from '../../utils/statusConfig';
import IconButton from '../ui/IconButton';

function Topbar({ onMenuClick }) {
  const { user, logout, getAccessToken } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getUnreadNotificationCount(getAccessToken())
      .then((result) => {
        if (!cancelled) setUnreadCount(result.unread_count);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-4 sm:px-6">
      <IconButton label="Open menu" onClick={onMenuClick} className="lg:hidden">
        <Menu className="size-5" aria-hidden="true" />
      </IconButton>

      <div className="min-w-0 flex-1" />

      <Link
        to="/notifications"
        className="relative flex size-9 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100"
        aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : 'Notifications'}
      >
        <Bell className="size-5" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-semibold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Link>

      <div className="hidden items-center gap-2 border-l border-slate-200 pl-3 sm:flex">
        <div className="text-right leading-tight">
          <p className="text-sm font-medium text-slate-800">{user?.full_name}</p>
          <p className="text-xs text-slate-500">{formatEnumLabel(user?.role)}</p>
        </div>
        <IconButton label="Log out" onClick={handleLogout}>
          <LogOut className="size-4.5" aria-hidden="true" />
        </IconButton>
      </div>
      <IconButton label="Log out" onClick={handleLogout} className="sm:hidden">
        <LogOut className="size-4.5" aria-hidden="true" />
      </IconButton>
    </header>
  );
}

export default Topbar;
