import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../../store/authStore';
import Login from './Login';

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('Login', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('stores tokens and user info after a successful login', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url) => {
        if (url.toString().includes('/auth/login')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                access_token: 'access123',
                refresh_token: 'refresh123',
                token_type: 'bearer',
                user: {
                  id: '1',
                  email: 'a@example.com',
                  full_name: 'A',
                  role: 'citizen',
                  district_id: null,
                  is_active: true,
                },
              }),
          });
        }
        return Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ error: { message: 'unexpected request' } }),
        });
      }),
    );

    renderLogin();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123!' } });
    fireEvent.click(screen.getByRole('button', { name: /log in/i }));

    await waitFor(() => {
      expect(localStorage.getItem('fsp_access_token')).toBe('access123');
    });
    expect(localStorage.getItem('fsp_refresh_token')).toBe('refresh123');
  });

  it('shows an error message on invalid credentials', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () =>
            Promise.resolve({ error: { code: 'INVALID_CREDENTIALS', message: 'Invalid email or password.' } }),
        }),
      ),
    );

    renderLogin();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /log in/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.');
    expect(localStorage.getItem('fsp_access_token')).toBeNull();
  });
});
