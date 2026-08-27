import { describe, expect, it } from 'vitest';
import { ROLES } from './constants';
import { dashboardPathForRole } from './permissions';

describe('dashboardPathForRole', () => {
  it('maps each role to its dashboard path', () => {
    expect(dashboardPathForRole(ROLES.CITIZEN)).toBe('/citizen');
    expect(dashboardPathForRole(ROLES.INSPECTOR)).toBe('/inspector');
    expect(dashboardPathForRole(ROLES.DISTRICT_OFFICER)).toBe('/officer');
    expect(dashboardPathForRole(ROLES.ADMIN)).toBe('/admin');
  });

  it('falls back to / for an unknown role', () => {
    expect(dashboardPathForRole('unknown')).toBe('/');
  });
});
