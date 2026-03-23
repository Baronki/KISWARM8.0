import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { DirectorAuth, checkBackendHealth } from "@/lib/kiwzb-api";

interface KIWZBContextType {
  isAuthenticated: boolean;
  auth: DirectorAuth | null;
  backendAvailable: boolean;
  login: (auth: DirectorAuth) => void;
  logout: () => void;
  checkBackend: () => Promise<boolean>;
}

const KIWZBContext = createContext<KIWZBContextType | undefined>(undefined);

export function KIWZBProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [auth, setAuth] = useState<DirectorAuth | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(false);

  // Check backend availability on mount
  useEffect(() => {
    checkBackendHealth().then(setBackendAvailable);
  }, []);

  const login = useCallback((directorAuth: DirectorAuth) => {
    setAuth(directorAuth);
    setIsAuthenticated(true);
    // Store in localStorage for persistence
    localStorage.setItem("kiwzb_auth", JSON.stringify(directorAuth));
  }, []);

  const logout = useCallback(() => {
    setAuth(null);
    setIsAuthenticated(false);
    localStorage.removeItem("kiwzb_auth");
  }, []);

  const checkBackend = useCallback(async () => {
    const available = await checkBackendHealth();
    setBackendAvailable(available);
    return available;
  }, []);

  // Restore auth from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("kiwzb_auth");
    if (stored) {
      try {
        const directorAuth = JSON.parse(stored);
        // Check if token is still valid
        if (new Date(directorAuth.expiresAt) > new Date()) {
          setAuth(directorAuth);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem("kiwzb_auth");
        }
      } catch (error) {
        console.error("Failed to restore auth:", error);
        localStorage.removeItem("kiwzb_auth");
      }
    }
  }, []);

  return (
    <KIWZBContext.Provider
      value={{
        isAuthenticated,
        auth,
        backendAvailable,
        login,
        logout,
        checkBackend,
      }}
    >
      {children}
    </KIWZBContext.Provider>
  );
}

export function useKIWZB() {
  const context = useContext(KIWZBContext);
  if (!context) {
    throw new Error("useKIWZB must be used within KIWZBProvider");
  }
  return context;
}
