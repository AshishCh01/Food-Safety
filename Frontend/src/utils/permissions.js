import {
  Bot,
  Building2,
  ClipboardList,
  FileText,
  History,
  LayoutDashboard,
  Map,
  PlusCircle,
  ScrollText,
  Users,
} from 'lucide-react';
import { DASHBOARD_PATH_BY_ROLE, ROLES } from './constants';

export function dashboardPathForRole(role) {
  return DASHBOARD_PATH_BY_ROLE[role] || '/';
}

// Role-aware primary navigation, consumed by components/layout/Sidebar.jsx.
// `end` marks a link that should only be "active" on an exact path match
// (otherwise the dashboard root link stays highlighted on every sub-route).
export const NAV_ITEMS_BY_ROLE = {
  [ROLES.CITIZEN]: [
    { label: 'Dashboard', path: '/citizen', icon: LayoutDashboard, end: true },
    { label: 'My Complaints', path: '/citizen/complaints', icon: FileText },
    { label: 'New Complaint', path: '/citizen/complaints/new', icon: PlusCircle },
  ],
  [ROLES.INSPECTOR]: [
    { label: 'Dashboard', path: '/inspector', icon: LayoutDashboard, end: true },
    { label: 'Assigned Cases', path: '/inspector/assignments', icon: ClipboardList },
    { label: 'Inspection History', path: '/inspector/history', icon: History },
    { label: 'Inspector Assistant', path: '/inspector/assistant', icon: Bot },
  ],
  [ROLES.DISTRICT_OFFICER]: [
    { label: 'Dashboard', path: '/officer', icon: LayoutDashboard, end: true },
    { label: 'Complaint Queue', path: '/officer/complaints', icon: ClipboardList },
    { label: 'Map', path: '/officer/map', icon: Map },
  ],
  [ROLES.ADMIN]: [
    { label: 'Dashboard', path: '/admin', icon: LayoutDashboard, end: true },
    { label: 'Staff', path: '/admin/staff', icon: Users },
    { label: 'Businesses', path: '/admin/businesses', icon: Building2 },
    { label: 'Knowledge Base', path: '/admin/rag-documents', icon: FileText },
    { label: 'Audit Logs', path: '/admin/audit-logs', icon: ScrollText },
  ],
};

export function navItemsForRole(role) {
  return NAV_ITEMS_BY_ROLE[role] || [];
}
