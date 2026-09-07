import { apiRequest, API_V1_BASE_URL } from './api';

export function getComplaintTriage(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/triage`, { token });
}

export function runComplaintTriage(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/triage`, { method: 'POST', token });
}

// AI Evidence Analysis Agent (Phase 7). Advisory only - see
// docs/AI_AGENTS_ARCHITECTURE.md section 5. Reading the latest result never
// triggers a new Gemini call. Running without `force` reuses an existing
// completed result instead of calling Gemini again.

export function getComplaintEvidenceAnalysis(complaintId, evidenceId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/evidence/${evidenceId}/analysis`, { token });
}

export function runComplaintEvidenceAnalysis(complaintId, evidenceId, token, { force = false } = {}) {
  const query = force ? '?force=true' : '';
  return apiRequest(`/officer/complaints/${complaintId}/evidence/${evidenceId}/analysis${query}`, {
    method: 'POST',
    token,
  });
}

export function getInspectionEvidenceAnalysis(inspectionId, evidenceId, token) {
  return apiRequest(`/inspector/inspections/${inspectionId}/evidence/${evidenceId}/analysis`, { token });
}

export function runInspectionEvidenceAnalysis(inspectionId, evidenceId, token, { force = false } = {}) {
  const query = force ? '?force=true' : '';
  return apiRequest(`/inspector/inspections/${inspectionId}/evidence/${evidenceId}/analysis${query}`, {
    method: 'POST',
    token,
  });
}

// AI Investigation Agent (Phase 9). Advisory case intelligence only - see
// docs/AI_AGENTS_ARCHITECTURE.md section 6. Reading the latest result never
// triggers a new Gemini call. Running without `force` reuses an existing
// completed brief instead of calling Gemini again.

export function getComplaintInvestigation(complaintId, token) {
  return apiRequest(`/officer/complaints/${complaintId}/investigation`, { token });
}

export function runComplaintInvestigation(complaintId, token, { force = false } = {}) {
  const query = force ? '?force=true' : '';
  return apiRequest(`/officer/complaints/${complaintId}/investigation${query}`, {
    method: 'POST',
    token,
  });
}

// Inspector Assistant (Phase 8). Advisory only - see
// docs/AI_AGENTS_ARCHITECTURE.md section 7. A conversation may be scoped to
// an inspection (case context) or general (regulatory Q&A only).

export function createAssistantConversation(token, { inspectionId } = {}) {
  return apiRequest('/inspector/assistant/conversations', {
    method: 'POST',
    token,
    body: { inspection_id: inspectionId || null },
  });
}

export function listAssistantConversations(token, { inspectionId } = {}) {
  const query = inspectionId ? `?inspection_id=${inspectionId}` : '';
  return apiRequest(`/inspector/assistant/conversations${query}`, { token });
}

export function getAssistantConversation(conversationId, token) {
  return apiRequest(`/inspector/assistant/conversations/${conversationId}`, { token });
}

export function sendAssistantMessage(conversationId, question, token) {
  return apiRequest(`/inspector/assistant/conversations/${conversationId}/messages`, {
    method: 'POST',
    token,
    body: { question },
  });
}

export async function sendAssistantMessageStream(conversationId, question, token, { onToken, onDone, onError }) {
  const url = `${API_V1_BASE_URL}/inspector/assistant/conversations/${conversationId}/messages/stream`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson?.error?.message || 'Failed to stream response');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const raw = trimmed.slice(6);
          try {
            const data = JSON.parse(raw);
            if (data.type === 'token' && onToken) {
              onToken(data.content);
            } else if (data.type === 'done' && onDone) {
              onDone(data);
            }
          } catch {
            if (onToken) onToken(raw);
          }
        }
      }
    }
  } catch (err) {
    if (onError) onError(err);
    else throw err;
  }
}

// Voice channel (LiveKit) - see docs/AI_AGENTS_ARCHITECTURE.md section 7.
// Mints a LiveKit room-join token for this conversation; the actual voice
// turns are handled by the LiveKit worker calling the backend directly, not
// by this frontend.
export function startLiveKitSession(conversationId, token) {
  return apiRequest(`/inspector/assistant/conversations/${conversationId}/livekit-session`, {
    method: 'POST',
    token,
  });
}