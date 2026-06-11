import { createContext } from "react";

export interface AgentClaims {
  sub: string;
  display_name?: string;
}

export interface AuthContextValue {
  token: string | null;
  agent: AgentClaims | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
