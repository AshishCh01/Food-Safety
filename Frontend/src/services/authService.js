import { apiRequest } from './api';

export function register({ email, password, fullName, phone }) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: { email, password, full_name: fullName, phone: phone || null },
  });
}

export function login({ email, password }) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: { email, password },
  });
}

export function refreshAccessToken(refreshToken) {
  return apiRequest('/auth/refresh', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  });
}

export function fetchCurrentUser(accessToken) {
  return apiRequest('/auth/me', { token: accessToken });
}

export function logout(accessToken) {
  return apiRequest('/auth/logout', { method: 'POST', token: accessToken });
}
