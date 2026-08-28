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

export function listAuditLogs(
  token,
  { action, entityType, entityId, actorUserId, page = 1, pageSize = 20 } = {}
) {
  return apiRequest(
    withQuery('/admin/audit-logs', {
      action,
      entity_type: entityType,
      entity_id: entityId,
      actor_user_id: actorUserId,
      page,
      page_size: pageSize,
    }),
    { token }
  );
}
