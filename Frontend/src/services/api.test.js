import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, SESSION_EXPIRED_EVENT, apiRequest } from './api';

const ACCESS_TOKEN_KEY = 'fsp_access_token';
const REFRESH_TOKEN_KEY = 'fsp_refresh_token';

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(handler) {
  const fetchMock = vi.fn(handler);
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function jsonResponse(status, body) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('apiRequest error handling', () => {
  it('throws an ApiError carrying the response status', async () => {
    stubFetch(() => jsonResponse(404, { error: { message: 'Complaint was not found.' } }));

    await expect(apiRequest('/officer/complaints/missing', { token: 'tok' })).rejects.toMatchObject({
      message: 'Complaint was not found.',
      status: 404,
    });
    await expect(apiRequest('/officer/complaints/missing', { token: 'tok' })).rejects.toBeInstanceOf(ApiError);
  });

  it('does not attempt a refresh for a 401 on an unauthenticated call (e.g. login)', async () => {
    const fetchMock = stubFetch(() => jsonResponse(401, { error: { message: 'Invalid credentials.' } }));

    await expect(apiRequest('/auth/login', { method: 'POST', body: {} })).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('does not attempt a refresh for a non-401 error', async () => {
    const fetchMock = stubFetch(() => jsonResponse(500, { error: { message: 'boom' } }));

    await expect(apiRequest('/officer/dashboard', { token: 'tok' })).rejects.toMatchObject({ status: 500 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe('apiRequest 401 refresh-and-retry', () => {
  it('silently refreshes and retries the original request on a 401', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'old-refresh-token');
    let dashboardCalls = 0;

    const fetchMock = stubFetch((url, options) => {
      const href = url.toString();
      if (href.includes('/officer/dashboard')) {
        dashboardCalls += 1;
        if (dashboardCalls === 1) {
          expect(options.headers.Authorization).toBe('Bearer stale-token');
          return jsonResponse(401, { error: { code: 'INVALID_TOKEN', message: 'Invalid or expired token.' } });
        }
        expect(options.headers.Authorization).toBe('Bearer fresh-token');
        return jsonResponse(200, { open_complaints: 3 });
      }
      if (href.includes('/auth/refresh')) {
        return jsonResponse(200, { access_token: 'fresh-token', refresh_token: 'new-refresh-token' });
      }
      throw new Error(`unexpected fetch: ${href}`);
    });

    const result = await apiRequest('/officer/dashboard', { token: 'stale-token' });

    expect(result).toEqual({ open_complaints: 3 });
    expect(dashboardCalls).toBe(2);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe('fresh-token');
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe('new-refresh-token');
  });

  it('shares a single refresh call across concurrent 401s (single-flight)', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'old-refresh-token');
    let refreshCalls = 0;

    stubFetch((url, options) => {
      const href = url.toString();
      if (href.includes('/auth/refresh')) {
        refreshCalls += 1;
        return jsonResponse(200, { access_token: 'fresh-token', refresh_token: 'new-refresh-token' });
      }
      if (options.headers.Authorization === 'Bearer stale-token') {
        return jsonResponse(401, { error: { message: 'Invalid or expired token.' } });
      }
      return jsonResponse(200, { ok: true });
    });

    const [a, b] = await Promise.all([
      apiRequest('/officer/complaints', { token: 'stale-token' }),
      apiRequest('/officer/inspectors', { token: 'stale-token' }),
    ]);

    expect(a).toEqual({ ok: true });
    expect(b).toEqual({ ok: true });
    expect(refreshCalls).toBe(1);
  });

  it('clears the stored session and notifies via SESSION_EXPIRED_EVENT when the refresh itself fails', async () => {
    localStorage.setItem(ACCESS_TOKEN_KEY, 'stale-token');
    localStorage.setItem(REFRESH_TOKEN_KEY, 'revoked-refresh-token');

    stubFetch((url) => {
      const href = url.toString();
      if (href.includes('/auth/refresh')) {
        return jsonResponse(401, { error: { code: 'INVALID_TOKEN', message: 'Invalid or expired token.' } });
      }
      return jsonResponse(401, { error: { message: 'Invalid or expired token.' } });
    });

    let sessionExpiredFired = false;
    window.addEventListener(SESSION_EXPIRED_EVENT, () => {
      sessionExpiredFired = true;
    });

    await expect(apiRequest('/officer/dashboard', { token: 'stale-token' })).rejects.toMatchObject({ status: 401 });

    expect(sessionExpiredFired).toBe(true);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
  });

  it('does not retry more than once even if the retried request also 401s', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'old-refresh-token');
    let dashboardCalls = 0;

    const fetchMock = stubFetch((url) => {
      const href = url.toString();
      if (href.includes('/auth/refresh')) {
        return jsonResponse(200, { access_token: 'fresh-token', refresh_token: 'new-refresh-token' });
      }
      dashboardCalls += 1;
      return jsonResponse(401, { error: { message: 'Invalid or expired token.' } });
    });

    await expect(apiRequest('/officer/dashboard', { token: 'stale-token' })).rejects.toMatchObject({ status: 401 });

    expect(dashboardCalls).toBe(2); // original + exactly one retry, no further refresh loop
    expect(fetchMock).toHaveBeenCalledTimes(3); // original + refresh + retry
  });

  it('rejects immediately with no refresh call when no refresh token is stored', async () => {
    const fetchMock = stubFetch(() => jsonResponse(401, { error: { message: 'Invalid or expired token.' } }));

    await expect(apiRequest('/officer/dashboard', { token: 'stale-token' })).rejects.toMatchObject({ status: 401 });

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
