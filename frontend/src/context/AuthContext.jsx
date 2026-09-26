import { createContext, useContext, useState, useCallback, useMemo } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export const ROLE_ADMIN = 1;
export const ROLE_MENTOR = 2;
export const ROLE_EMPLOYEE = 3;
export const ROLE_INTERN = 4;
export const ROLE_TRAINEE = 5;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (username, password) => {
    const { data } = await api.post("/auth/login", {
      Username: username,
      Password: password,
    });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  const refreshMe = useCallback(async () => {
    const { data } = await api.get("/auth/me");
    setUser((prev) => {
      const merged = { ...prev, ...data };
      localStorage.setItem("user", JSON.stringify(merged));
      return merged;
    });
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isAdmin: user?.RoleID === ROLE_ADMIN,
      isMentor: user?.RoleID === ROLE_MENTOR,
      login,
      logout,
      refreshMe,
    }),
    [user, login, logout, refreshMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
