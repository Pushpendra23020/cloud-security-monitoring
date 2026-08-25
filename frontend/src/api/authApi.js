import apiClient from "./client";

export const getAuthStatus = async () => (await apiClient.get("/auth/status")).data;
export const login = async (credentials) => (await apiClient.post("/auth/login", credentials)).data;
export const getCurrentUser = async () => (await apiClient.get("/auth/me")).data;
