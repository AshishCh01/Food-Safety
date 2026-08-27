import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ROLES } from '../utils/constants';
import RoleRoute from './RoleRoute';

const mockUseAuth = vi.fn();
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

function renderWithRole(initialPath) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/citizen" element={<div>Citizen Dashboard</div>} />
        <Route element={<RoleRoute allowedRoles={[ROLES.ADMIN]} />}>
          <Route path="/admin" element={<div>Admin Page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('RoleRoute', () => {
  it("redirects to the user's own dashboard when the role is not allowed", () => {
    mockUseAuth.mockReturnValue({ user: { role: ROLES.CITIZEN } });

    renderWithRole('/admin');

    expect(screen.getByText('Citizen Dashboard')).toBeInTheDocument();
  });

  it('renders the nested route when the role is allowed', () => {
    mockUseAuth.mockReturnValue({ user: { role: ROLES.ADMIN } });

    renderWithRole('/admin');

    expect(screen.getByText('Admin Page')).toBeInTheDocument();
  });

  it('redirects to login when there is no user', () => {
    mockUseAuth.mockReturnValue({ user: null });

    renderWithRole('/admin');

    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });
});
