import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { login as loginApi, logout as logoutApi, me, register as registerApi } from "../api/auth";
import { getToken } from "../api/client";
import type { User } from "../types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    if (!getToken()) {
      setUser(null);
      return;
    }
    const profile = await me();
    setUser(profile);
  }

  useEffect(() => {
    refresh()
      .catch(() => {
        logoutApi();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      async login(email, password) {
        const data = await loginApi(email, password);
        setUser(data.user);
      },
      async register(name, email, password) {
        const data = await registerApi(name, email, password);
        setUser(data.user);
      },
      logout() {
        logoutApi();
        setUser(null);
      },
      refresh,
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
