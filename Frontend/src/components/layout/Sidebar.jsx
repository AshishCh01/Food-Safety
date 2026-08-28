import { ShieldCheck, X } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { useAuth } from '../../hooks/useAuth';
import { navItemsForRole } from '../../utils/permissions';
import IconButton from '../ui/IconButton';

/** Nav-list content shared by the desktop persistent sidebar and the mobile
 * Drawer (see AppShell.jsx). `onNavigate` closes the drawer on mobile after
 * a link is clicked; passing `onClose` also renders a close button (mobile only). */
function Sidebar({ onNavigate, onClose }) {
  const { user } = useAuth();
  const items = navItemsForRole(user?.role);

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-2 px-4 text-white">
        <ShieldCheck className="size-6 shrink-0" aria-hidden="true" />
        <span className="min-w-0 flex-1 text-sm font-semibold leading-tight">
          Maharashtra Food Safety Platform
        </span>
        {onClose && (
          <IconButton label="Close menu" onClick={onClose} className="text-brand-100 hover:bg-brand-800">
            <X className="size-4.5" aria-hidden="true" />
          </IconButton>
        )}
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-2">
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-800 text-white'
                  : 'text-brand-100 hover:bg-brand-800/60 hover:text-white',
              )
            }
          >
            <item.icon className="size-4.5 shrink-0" aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export default Sidebar;
