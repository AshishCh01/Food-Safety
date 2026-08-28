import { apiRequest } from './api';

export function getOfficerAnalytics(token, { trendDays = 30 } = {}) {
  return apiRequest(`/officer/analytics?trend_days=${trendDays}`, { token });
}

export function getAdminAnalytics(token, { trendDays = 30 } = {}) {
  return apiRequest(`/admin/analytics?trend_days=${trendDays}`, { token });
}
