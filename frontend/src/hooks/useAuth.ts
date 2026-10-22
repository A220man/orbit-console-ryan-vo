/** Authentication hook and context */

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { api } from '../api/client';
import type { UserInfo, OIDCConfig } from '../types';

interface AuthContextType {
  user: UserInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (redirectUri?: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  oidcConfig: OIDCConfig | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [oidcConfig, setOidcConfig] = useState<OIDCConfig | null>(null);

  const checkAuth = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = api.getToken();
      if (!token) {
        setUser(null);
        return;
      }

      const userInfo = await api.getCurrentUser();
      setUser(userInfo);
    } catch (error) {
      console.error('Auth check failed:', error);
      api.clearToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadConfig = useCallback(async () => {
    try {
      const config = await api.getOIDCConfig();
      setOidcConfig(config);
    } catch (error) {
      console.error('Failed to load OIDC config:', error);
    }
  }, []);

  useEffect(() => {
    loadConfig();
    checkAuth();
  }, [checkAuth, loadConfig]);

  const login = useCallback((redirectUri?: string) => {
    const params = new URLSearchParams();
    if (redirectUri) params.set('redirect_uri', redirectUri);
    window.location.href = `/api/v1/auth/login?${params.toString()}`;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      api.clearToken();
      setUser(null);
    }
  }, []);

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    checkAuth,
    oidcConfig,
  };

  return React.createElement(
    AuthContext.Provider,
    { value },
    children
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
