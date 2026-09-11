import { apiRequest } from './api';

export function createLegalAction(complaintId, payload, token) {
  return apiRequest(`/officer/complaints/${complaintId}/legal-actions`, {
    method: 'POST',
    token,
    body: payload,
  });
}

export function listLegalActions(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/legal-actions`, { token });
}

export function updateLegalAction(actionId, payload, token) {
  return apiRequest(`/officer/legal-actions/${actionId}`, {
    method: 'PATCH',
    token,
    body: payload,
  });
}
