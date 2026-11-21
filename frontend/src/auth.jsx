import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getTokens, setTokens } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getTokens()) {
      setLoading(false);
      return;
    }
    api("/auth/me/")
      .then(setUser)
      .catch(() => setTokens(null))
      .finally(() => setLoading(false));
  }, []);

  // Если сервер отозвал сессию, интерфейс сразу переходит в режим гостя
  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await api("/auth/login/", { method: "POST", body: { email, password } });
    setTokens({ access: data.access, refresh: data.refresh });
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (email, password, role) => {
    const data = await api("/auth/register/", { method: "POST", body: { email, password, role } });
    setTokens({ access: data.access, refresh: data.refresh });
    setUser(data.user);
    return data.user;
  }, []);

  // F-04/F-05: перечитать пользователя после подтверждения email или правки профиля
  const refreshUser = useCallback(async () => {
    const data = await api("/auth/me/");
    setUser(data);
    return data;
  }, []);

  const logout = useCallback(async () => {
    const tokens = getTokens();
    try {
      if (tokens?.refresh) await api("/auth/logout/", { method: "POST", body: { refresh: tokens.refresh } });
    } finally {
      setTokens(null);
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, refreshUser, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
