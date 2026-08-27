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

export function listDistricts(token) {
  return apiRequest('/districts', { token });
}

export function listComplaintCategories(token) {
  return apiRequest('/complaint-categories', { token });
}

export function createComplaint(payload, token) {
  return apiRequest('/complaints', { method: 'POST', token, body: payload });
}

export function listMyComplaints(token, { status, categoryId, page = 1, pageSize = 20 } = {}) {
  return apiRequest(
    withQuery('/complaints/my', { status, category_id: categoryId, page, page_size: pageSize }),
    { token }
  );
}

export function getComplaint(complaintId, token) {
  return apiRequest(`/complaints/${complaintId}`, { token });
}

export function getComplaintTimeline(complaintId, token) {
  return apiRequest(`/complaints/${complaintId}/timeline`, { token });
}

export function listEvidence(complaintId, token) {
  return apiRequest(`/complaints/${complaintId}/evidence`, { token });
}

export function uploadEvidence(complaintId, file, token, { capturedAt, latitude, longitude } = {}) {
  const form = new FormData();
  form.append('file', file);
  if (capturedAt) form.append('captured_at', capturedAt);
  if (latitude !== undefined && latitude !== null) form.append('latitude', latitude);
  if (longitude !== undefined && longitude !== null) form.append('longitude', longitude);

  return apiRequest(`/complaints/${complaintId}/evidence`, { method: 'POST', token, body: form });
}

export function listDistrictComplaints(
  token,
  { status, priority, categoryId, page = 1, pageSize = 20 } = {}
) {
  return apiRequest(
    withQuery('/officer/complaints', {
      status,
      priority,
      category_id: categoryId,
      page,
      page_size: pageSize,
    }),
    { token }
  );
}

export function getDistrictComplaint(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}`, { token });
}

export function getDistrictComplaintTimeline(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/timeline`, { token });
}

export function listDistrictComplaintEvidence(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/evidence`, { token });
}

export function updateComplaintStatus(complaintId, { status, reason }, token) {
  return apiRequest(`/officer/complaints/${complaintId}/status`, {
    method: 'PATCH',
    token,
    body: { status, reason: reason || null },
  });
}

export function assignInspector(complaintId, { inspectorStaffId, dueAt, notes }, token) {
  return apiRequest(`/officer/complaints/${complaintId}/assign`, {
    method: 'POST',
    token,
    body: { inspector_staff_id: inspectorStaffId, due_at: dueAt || null, notes: notes || null },
  });
}

export function getComplaintAssignment(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/assignment`, { token });
}

export function getComplaintInspection(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/inspection`, { token });
}

export function listInspectors(token) {
  return apiRequest('/officer/inspectors', { token });
}
