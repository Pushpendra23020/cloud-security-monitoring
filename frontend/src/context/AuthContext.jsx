import { useEffect, useState } from "react";
import {
  getAuthStatus,
  getCurrentUser,
  listOrganizations,
  login as loginRequest,
  logout as logoutRequest,
  refreshSession,
  switchOrganization as switchOrganizationRequest,
  verifyMfaChallenge,
} from "../api/authApi";
import { setAccessToken } from "../api/client";
import { AuthContext } from "./authState";

async function getAuthenticatedSession() {
  const [user, organizations] = await Promise.all([
    getCurrentUser(),
    listOrganizations(),
  ]);
  return { user, organizations };
}

export function AuthProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [oidcEnabled, setOidcEnabled] = useState(false);
  const [oidcLoginUrl, setOidcLoginUrl] = useState(null);
  const [user, setUser] = useState(null);
  const [organizations, setOrganizations] = useState([]);

  const currentOrganization = organizations.find((item) => item.is_current) || null;

  useEffect(() => {
    let active = true;
    const initialize = async () => {
      try {
        const status = await getAuthStatus();
        if (!active) return;
        setEnabled(status.enabled);
        setOidcEnabled(status.oidc_enabled);
        setOidcLoginUrl(status.oidc_login_url);
        localStorage.removeItem("cloud-sentinel-token");
        if (status.enabled) {
          const token = await refreshSession();
          setAccessToken(token.access_token);
          const session = await getAuthenticatedSession();
          if (!active) return;
          setUser(session.user);
          setOrganizations(session.organizations);
        }
      } catch {
        setAccessToken(null);
        if (active) {
          setUser(null);
          setOrganizations([]);
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    initialize();
    const expire = () => {
      setAccessToken(null);
      setUser(null);
      setOrganizations([]);
    };
    window.addEventListener("cloud-sentinel-auth-expired", expire);
    return () => {
      active = false;
      window.removeEventListener("cloud-sentinel-auth-expired", expire);
    };
  }, []);

  const login = async (username, password) => {
    const token = await loginRequest({ username, password });
    if (token.mfa_required) return token;
    setAccessToken(token.access_token);
    try {
      const session = await getAuthenticatedSession();
      setUser(session.user);
      setOrganizations(session.organizations);
    } catch (error) {
      setAccessToken(null);
      setUser(null);
      setOrganizations([]);
      throw error;
    }
    return token;
  };

  const completeMfa = async (challengeToken, code) => {
    const token = await verifyMfaChallenge(challengeToken, code);
    setAccessToken(token.access_token);
    try {
      const session = await getAuthenticatedSession();
      setUser(session.user);
      setOrganizations(session.organizations);
    } catch (error) {
      setAccessToken(null);
      setUser(null);
      setOrganizations([]);
      throw error;
    }
  };

  const switchOrganization = async (organizationId) => {
    const target = organizations.find(
      (organization) => organization.organization_id === organizationId
    );
    if (!target) throw new Error("Organization is not available.");
    if (target.is_current) return;

    const token = await switchOrganizationRequest(organizationId);
    if (!token?.access_token) throw new Error("Organization switch did not return a valid session.");

    setAccessToken(token.access_token);
    const session = await getAuthenticatedSession();
    setUser(session.user);
    setOrganizations(session.organizations);
  };

  const logout = async () => {
    try {
      await logoutRequest();
    } finally {
      setAccessToken(null);
      setUser(null);
      setOrganizations([]);
    }
  };

  return <AuthContext.Provider value={{
    enabled,
    oidcEnabled,
    oidcLoginUrl,
    loading,
    user,
    organizations,
    currentOrganization,
    login,
    completeMfa,
    logout,
    switchOrganization,
  }}>
    {children}
  </AuthContext.Provider>;
}
