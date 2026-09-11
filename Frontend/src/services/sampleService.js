import { apiRequest } from './api';

export function collectSample(inspectionId, payload, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}/samples`, {
    method: 'POST',
    token,
    body: payload,
  });
}

export function listSamplesForInspection(inspectionId, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}/samples`, { token });
}

export function dispatchSample(sampleId, payload, token) {
  return apiRequest(`/inspector/samples/${sampleId}/dispatch`, {
    method: 'POST',
    token,
    body: payload,
  });
}
