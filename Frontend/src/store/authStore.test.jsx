import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../hooks/useAuth';
import { SESSION_EXPIRED_EVENT } from '../services/api';
import { AuthProvider } from './authStore';

function Probe() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div>loading</div>;
  return <div>{user ? `signed-in:${user.email}` : 'signed-out'}</div>;
}

function renderApp() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );
}

describe('AuthProvider session restoration', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('persists the rotated refresh token (not just the access token) after a silent refresh', async () => {
    // Simulates an app reload with an expired access token still in
    // storage: /auth/me fails once, the store falls back to /auth/refresh,
    // then retries /auth/me with the new access token.
    localStorage.setItem('fsp_access_token', 'stale-access-token');
    localStorage.setItem('fsp_refresh_token', 'original-refresh-token');

    let meCallCount = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn((url) => {
        const href = url.toString();
        if (href.includes('/auth/me')) {
          meCallCount += 1;
          if (meCallCount === 1) {
            // First call uses the stale access token still in storage -
            // simulates it having expired.
            return Promise.resolve({
              ok: false,
              status: 401,
              json: () => Promise.resolve({ error: { code: 'INVALID_TOKEN', message: 'Invalid or expired token.' } }),
            });
          }
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                id: '1',
                email: 'restored@example.com',
                full_name: 'Restored User',
                role: 'citizen',
                district_id: null,
                is_active: true,
              }),
          });
        }
        if (href.includes('/auth/refresh')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                access_token: 'rotated-access-token',
                refresh_token: 'rotated-refresh-token',
                token_type: 'bearer',
              }),
          });
        }
        return Promise.resolve({
          ok: false,
          status: 404,
          json: () => Promise.resolve({ error: { message: 'unexpected request' } }),
        });
      }),
    );

    renderApp();

    await screen.findByText('signed-in:restored@example.com');

    // The server rotates and revokes the presented refresh token on every
    // use (docs/SECURITY_AND_RBAC.md section 18) - if the client only
    // stored the new access token, the next refresh attempt would present
    // an already-revoked refresh token and be rejected.
    expect(localStorage.getItem('fsp_access_token')).toBe('rotated-access-token');
    expect(localStorage.getItem('fsp_refresh_token')).toBe('rotated-refresh-token');
  });

  it('clears the session when refresh itself fails (e.g. the stored refresh token was revoked)', async () => {
    localStorage.setItem('fsp_access_token', 'stale-access-token');
    localStorage.setItem('fsp_refresh_token', 'revoked-refresh-token');

    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ error: { code: 'INVALID_TOKEN', message: 'Invalid or expired token.' } }),
        }),
      ),
    );

    renderApp();

    await waitFor(() => {
      expect(screen.getByText('signed-out')).toBeInTheDocument();
    });
    expect(localStorage.getItem('fsp_access_token')).toBeNull();
    expect(localStorage.getItem('fsp_refresh_token')).toBeNull();
  });
});

describe('AuthProvider session-expired event', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('clears the signed-in user when services/api.js dispatches SESSION_EXPIRED_EVENT', async () => {
    // Simulates a mid-session access-token expiry that the api.js 401
    // handler could not silently recover from (see api.test.js for that
    // refresh-and-retry logic) - by the time this fires, api.js has already
    // cleared localStorage itself; this only needs to prove the React
    // `user` state (what ProtectedRoute actually checks) clears too.
    localStorage.setItem('fsp_access_token', 'still-valid-at-mount-token');
    localStorage.setItem('fsp_refresh_token', 'some-refresh-token');

    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              id: '1',
              email: 'active@example.com',
              full_name: 'Active User',
              role: 'citizen',
              district_id: null,
              is_active: true,
            }),
        }),
      ),
    );

    renderApp();

    await screen.findByText('signed-in:active@example.com');

    act(() => {
      window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
    });

    await waitFor(() => {
      expect(screen.getByText('signed-out')).toBeInTheDocument();
    });
  });
});
