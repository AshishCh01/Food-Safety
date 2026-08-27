import { DASHBOARD_PATH_BY_ROLE } from './constants';

export function dashboardPathForRole(role) {
  return DASHBOARD_PATH_BY_ROLE[role] || '/';
}
