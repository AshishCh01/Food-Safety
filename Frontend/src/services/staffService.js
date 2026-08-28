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

export function createStaff(payload, token) {
  return apiRequest('/admin/staff', {
    method: 'POST',
    token,
    body: {
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName,
      phone: payload.phone || null,
      role: payload.role,
      district_id: payload.districtId,
      employee_code: payload.employeeCode,
      designation: payload.designation || null,
    },
  });
}

export function listUsers(token, { role, isActive, page = 1, pageSize = 20 } = {}) {
  return apiRequest(withQuery('/admin/users', { role, is_active: isActive, page, page_size: pageSize }), { token });
}

export function updateUserStatus(userId, isActive, token) {
  return apiRequest(`/admin/users/${userId}/status`, {
    method: 'PATCH',
    token,
    body: { is_active: isActive },
  });
}
