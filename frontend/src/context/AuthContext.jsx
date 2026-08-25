import { useEffect, useState } from "react";
import { getAuthStatus, getCurrentUser, login as loginRequest } from "../api/authApi";
import { AuthContext } from "./authState";

export function AuthProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    let active = true;
    const initialize = async () => {
      try {
        const status = await getAuthStatus();
        if (!active) return;
        setEnabled(status.enabled);
        const token = localStorage.getItem("cloud-sentinel-token");
        if (status.enabled && token) setUser(await getCurrentUser());
      } catch {
        localStorage.removeItem("cloud-sentinel-token");
      } finally {
        if (active) setLoading(false);
      }
    };
    initialize();
    const expire = () => setUser(null);
    window.addEventListener("cloud-sentinel-auth-expired", expire);
    return () => {
      active = false;
      window.removeEventListener("cloud-sentinel-auth-expired", expire);
    };
  }, []);

  const login = async (username, password) => {
    const token = await loginRequest({ username, password });
    localStorage.setItem("cloud-sentinel-token", token.access_token);
    setUser(await getCurrentUser());
  };

  const logout = () => {
    localStorage.removeItem("cloud-sentinel-token");
    setUser(null);
  };

  return <AuthContext.Provider value={{ enabled, loading, user, login, logout }}>
    {children}
  </AuthContext.Provider>;
}
