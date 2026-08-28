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

export function listBusinesses(token, { q, districtId, page = 1, pageSize = 20 } = {}) {
  return apiRequest(withQuery('/businesses', { q, district_id: districtId, page, page_size: pageSize }), { token });
}

export function getBusiness(businessId, token) {
  return apiRequest(`/businesses/${businessId}`, { token });
}
