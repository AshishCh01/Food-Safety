import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import ProtectedRoute from './ProtectedRoute';

const mockUseAuth = vi.fn();
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

function renderWithRoute(initialPath) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/secret" element={<div>Secret Page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('ProtectedRoute', () => {
  it('redirects to /login when not authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false });

    renderWithRoute('/secret');

    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('renders the nested route when authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false });

    renderWithRoute('/secret');

    expect(screen.getByText('Secret Page')).toBeInTheDocument();
  });

  it('shows a loading state while the session is being restored', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: true });

    renderWithRoute('/secret');

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
