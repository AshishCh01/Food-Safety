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

export function listFoodAnalysts(token) {
  return apiRequest('/food-analysts', { token });
}

export function listAnalystSamples(token, { status, page = 1, pageSize = 20 } = {}) {
  return apiRequest(withQuery('/food-analyst/samples', { status, page, page_size: pageSize }), { token });
}

export function receiveSample(sampleId, token) {
  return apiRequest(`/food-analyst/samples/${sampleId}/receive`, { method: 'POST', token });
}

export function submitResult(sampleId, payload, token) {
  return apiRequest(`/food-analyst/samples/${sampleId}/result`, {
    method: 'POST',
    token,
    body: payload,
  });
}
