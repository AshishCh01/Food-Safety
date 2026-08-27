import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  refreshAccessToken,
} from '../services/authService';
import { AuthContext } from './AuthContext';

const ACCESS_TOKEN_KEY = 'fsp_access_token';
const REFRESH_TOKEN_KEY = 'fsp_refresh_token';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      try {
        const me = await fetchCurrentUser(accessToken);
        if (isMounted) setUser(me);
      } catch {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (refreshToken) {
          try {
            const tokens = await refreshAccessToken(refreshToken);
            localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
            const me = await fetchCurrentUser(tokens.access_token);
            if (isMounted) setUser(me);
          } catch {
            clearSession();
          }
        } else {
          clearSession();
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, [clearSession]);

  const login = useCallback(async (email, password) => {
    const data = await loginRequest({ email, password });
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (accessToken) {
      try {
        await logoutRequest(accessToken);
      } catch {
        // Stateless JWT: logout is best-effort server-side. The token is
        // discarded client-side regardless.
      }
    }
    clearSession();
  }, [clearSession]);

  const getAccessToken = useCallback(() => localStorage.getItem(ACCESS_TOKEN_KEY), []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      getAccessToken,
    }),
    [user, isLoading, login, logout, getAccessToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
