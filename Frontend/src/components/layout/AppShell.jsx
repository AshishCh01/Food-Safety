import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Drawer from '../ui/Drawer';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

/** Layout for every authenticated (citizen/inspector/officer/admin) route:
 * a persistent sidebar on desktop, collapsing into a Drawer on mobile,
 * plus a shared Topbar. Nested under ProtectedRoute in routes/AppRoutes.jsx. */
function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="hidden w-64 shrink-0 bg-brand-900 lg:block">
        <Sidebar />
      </aside>

      <Drawer
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        side="left"
        widthClassName="max-w-64"
        bare
      >
        <div className="h-full bg-brand-900">
          <Sidebar
            onNavigate={() => setMobileNavOpen(false)}
            onClose={() => setMobileNavOpen(false)}
          />
        </div>
      </Drawer>

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppShell;
