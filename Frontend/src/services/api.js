const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_V1_BASE_URL = `${API_BASE_URL}/api/v1`;

const ACCESS_TOKEN_KEY = 'fsp_access_token';
const REFRESH_TOKEN_KEY = 'fsp_refresh_token';

// Dispatched on `window` when a silent refresh-and-retry fails (no refresh
// token stored, or the backend rejects it - e.g. revoked/expired). AuthProvider
// (src/store/authStore.jsx) listens for this to clear its React `user` state,
// which is what actually drives ProtectedRoute's redirect to /login - api.js
// has no router access of its own, so it only ever touches localStorage and
// notifies via this event rather than navigating directly.
export const SESSION_EXPIRED_EVENT = 'fsp:session-expired';

// Thrown by apiRequest instead of a plain Error so callers (and the 401
// handler below) can branch on the HTTP status rather than parsing the
// message string.
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new ApiError(`Health check failed with status ${response.status}`, response.status);
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

async function throwApiError(response) {
  throw new ApiError(await parseErrorMessage(response), response.status);
}

function clearStoredSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Concurrent 401s (e.g. a dashboard firing several requests at once) must
// share a single refresh attempt: the backend rotates and revokes the
// refresh token on every use (docs/SECURITY_AND_RBAC.md section 19), so two
// independent refresh calls presenting the same token would have only one
// winner, forcing the other into a spurious logout. This module-level
// promise makes every caller await the same in-flight attempt instead.
let refreshPromise = null;

function refreshSession() {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      return Promise.reject(new ApiError('No refresh token available.', 401));
    }

    // Calls apiRequest directly rather than a separate raw fetch - safe
    // from recursion because this request has no `token`, so the 401-retry
    // branch below never re-enters for it even if the refresh itself fails.
    refreshPromise = apiRequest('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    })
      .then((tokens) => {
        // The rotated refresh token must be persisted too, not just the new
        // access token - see the matching comment in store/authStore.jsx.
        localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
        return tokens.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

// Thin wrapper around fetch for the versioned backend API. The backend is
// the authorization boundary; this helper only attaches the bearer token
// and normalizes error responses, never client-side role/district logic.
//
// On a 401 from an authenticated call (one that was sent with a `token`),
// it transparently attempts one silent refresh-and-retry before giving up -
// without this, an access token expiring mid-session (they're short-lived,
// see docs/SECURITY_AND_RBAC.md section 19) surfaced as an opaque generic
// error on whatever page the user happened to be on, instead of either
// recovering silently or sending them back to /login.
export async function apiRequest(path, { method = 'GET', token, body, _isRetry = false } = {}) {
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
    if (response.status === 401 && token && !_isRetry) {
      try {
        const newToken = await refreshSession();
        return apiRequest(path, { method, token: newToken, body, _isRetry: true });
      } catch {
        clearStoredSession();
        window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
      }
    }
    await throwApiError(response);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
