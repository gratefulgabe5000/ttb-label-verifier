import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { AUTH_TOKEN_KEY, AUTH_UNAUTHORIZED_EVENT, authApi } from "@/lib/api-client";
import { AuthContext, type AgentClaims, type AuthContextValue } from "./auth-context";

function decodeAgentClaims(token: string): AgentClaims | null {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as AgentClaims;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(AUTH_TOKEN_KEY));

  const login = useCallback(async (username: string, password: string) => {
    const response = await authApi.login({ username, password });
    localStorage.setItem(AUTH_TOKEN_KEY, response.access_token);
    setToken(response.access_token);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
  }, []);

  // A 401 from any API call means the stored token is expired/invalid —
  // clear it so ProtectedRoute redirects to /login.
  useEffect(() => {
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const agent = useMemo(() => (token ? decodeAgentClaims(token) : null), [token]);

  const value = useMemo<AuthContextValue>(
    () => ({ token, agent, isAuthenticated: token !== null, login, logout }),
    [token, agent, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
