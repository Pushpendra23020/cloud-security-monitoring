import apiClient from "./client";

export const getAuthStatus = async () => (await apiClient.get("/auth/status")).data;
export const login = async (credentials) => (await apiClient.post("/auth/login", credentials)).data;
export const refreshSession = async () => (await apiClient.post("/auth/refresh")).data;
export const logout = async () => apiClient.post("/auth/logout");
export const getCurrentUser = async () => (await apiClient.get("/auth/me")).data;
export const listOrganizations = async () => (await apiClient.get("/auth/organizations")).data;
export const switchOrganization = async (organizationId) => (
  await apiClient.post("/auth/switch-organization", { organization_id: organizationId })
).data;
export const listSessions = async () => (await apiClient.get("/auth/sessions")).data;
export const revokeSession = async (sessionId) => apiClient.delete(`/auth/sessions/${sessionId}`);
export const verifyMfaChallenge = async (challengeToken, code) => (
  await apiClient.post("/auth/mfa/verify", { challenge_token: challengeToken, code })
).data;
export const getMfaStatus = async () => (await apiClient.get("/auth/mfa/status")).data;
export const beginMfaSetup = async () => (await apiClient.post("/auth/mfa/setup")).data;
export const enableMfa = async (code) => (await apiClient.post("/auth/mfa/enable", { code })).data;
export const disableMfa = async (password, code) => apiClient.post("/auth/mfa/disable", { password, code });
export const regenerateRecoveryCodes = async (code) => (
  await apiClient.post("/auth/mfa/recovery-codes", { code })
).data;
