import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, setToken, setUnauthorizedHandler } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // the /me response, or null when logged out
  const [loading, setLoading] = useState(true); // true while we check a saved token on page load

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout); // an expired token anywhere logs the user out
    if (!localStorage.getItem("token")) {
      setLoading(false);
      return;
    }
    api.get("/me").then(setUser).catch(logout).finally(() => setLoading(false));
  }, [logout]);

  const login = async (username, password) => {
    const { access_token } = await api.login(username, password);
    setToken(access_token);
    const me = await api.get("/me");
    setUser(me);
    return me;
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isFaculty: user?.role === "faculty",
    isCoordinator: !!user && user.role !== "faculty",
    canWrite: !!user?.can_write,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
