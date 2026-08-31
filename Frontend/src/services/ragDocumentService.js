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

export function uploadRagDocument(payload, file, token) {
  const formData = new FormData();
  formData.set('file', file);
  formData.set('title', payload.title);
  formData.set('document_type', payload.documentType);
  if (payload.sourceOrganization) formData.set('source_organization', payload.sourceOrganization);
  if (payload.version) formData.set('version', payload.version);
  if (payload.effectiveDate) formData.set('effective_date', payload.effectiveDate);
  if (payload.sourceUrl) formData.set('source_url', payload.sourceUrl);
  if (payload.businessType) formData.set('business_type', payload.businessType);
  if (payload.jurisdiction) formData.set('jurisdiction', payload.jurisdiction);

  return apiRequest('/admin/rag/documents', { method: 'POST', token, body: formData });
}

export function listRagDocuments(token, { status, documentType, isActive, page = 1, pageSize = 20 } = {}) {
  return apiRequest(
    withQuery('/admin/rag/documents', {
      status,
      document_type: documentType,
      is_active: isActive,
      page,
      page_size: pageSize,
    }),
    { token },
  );
}

export function getRagDocument(documentId, token) {
  return apiRequest(`/admin/rag/documents/${documentId}`, { token });
}

export function ingestRagDocument(documentId, token) {
  return apiRequest(`/admin/rag/documents/${documentId}/ingest`, { method: 'POST', token });
}

export function deactivateRagDocument(documentId, token) {
  return apiRequest(`/admin/rag/documents/${documentId}/deactivate`, { method: 'POST', token });
}

export function deleteRagDocument(documentId, token) {
  return apiRequest(`/admin/rag/documents/${documentId}`, { method: 'DELETE', token });
}
