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

export function listAssignments(token, { status, page = 1, pageSize = 20 } = {}) {
  return apiRequest(withQuery('/inspector/assignments', { status, page, page_size: pageSize }), { token });
}

export function getAssignment(assignmentId, token) {
  return apiRequest(`/inspector/assignments/${assignmentId}`, { token });
}

export function createInspection(payload, token) {
  return apiRequest('/inspector/inspections', {
    method: 'POST',
    token,
    body: { complaint_id: payload.complaintId, scheduled_at: payload.scheduledAt || null },
  });
}

export function startInspection(inspectionId, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}`, {
    method: 'PATCH',
    token,
    body: { status: 'in_progress' },
  });
}

export function updateInspection(inspectionId, { scheduledAt, summary, actionRecommended }, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}`, {
    method: 'PATCH',
    token,
    body: {
      scheduled_at: scheduledAt || null,
      summary: summary || null,
      action_recommended: actionRecommended || null,
    },
  });
}

export function addFinding(inspectionId, payload, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}/findings`, {
    method: 'POST',
    token,
    body: {
      check_code: payload.checkCode,
      finding: payload.finding,
      severity: payload.severity,
      compliant: payload.compliant,
      notes: payload.notes || null,
      corrective_action: payload.correctiveAction || null,
    },
  });
}

export function uploadInspectionEvidence(inspectionId, file, token) {
  const form = new FormData();
  form.append('file', file);
  return apiRequest(`/inspector/inspections/${inspectionId}/evidence`, { method: 'POST', token, body: form });
}

export function listInspectionEvidence(inspectionId, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}/evidence`, { token });
}

export function completeInspection(inspectionId, { summary, actionRecommended }, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}/complete`, {
    method: 'POST',
    token,
    body: { summary, action_recommended: actionRecommended },
  });
}

export function listInspectionHistory(token, { page = 1, pageSize = 20 } = {}) {
  return apiRequest(withQuery('/inspector/history', { page, page_size: pageSize }), { token });
}
