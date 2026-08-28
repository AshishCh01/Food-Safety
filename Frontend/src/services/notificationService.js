import { apiRequest } from './api';

function withQuery(path, params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value);
    }
  });
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export function listNotifications(token, { isRead, page = 1, pageSize = 20 } = {}) {
  return apiRequest(withQuery('/notifications', { is_read: isRead, page, page_size: pageSize }), { token });
}

export function getUnreadNotificationCount(token) {
  return apiRequest('/notifications/unread-count', { token });
}

export function markNotificationRead(notificationId, token) {
  return apiRequest(`/notifications/${notificationId}/read`, { method: 'PATCH', token });
}

export function markAllNotificationsRead(token) {
  return apiRequest('/notifications/read-all', { method: 'POST', token });
}
