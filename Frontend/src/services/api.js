const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_V1_BASE_URL = `${API_BASE_URL}/api/v1`;

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json();
}

async function parseErrorMessage(response) {
  try {
    const data = await response.json();
    return data?.error?.message || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

// Thin wrapper around fetch for the versioned backend API. The backend is
// the authorization boundary; this helper only attaches the bearer token
// and normalizes error responses, never client-side role/district logic.
export async function apiRequest(path, { method = 'GET', token, body } = {}) {
  const isFormData = body instanceof FormData;

  const response = await fetch(`${API_V1_BASE_URL}${path}`, {
    method,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
