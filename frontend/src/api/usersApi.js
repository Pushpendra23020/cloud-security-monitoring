import apiClient from "./client";

export const listUsers = async () => (await apiClient.get("/users")).data;
export const listAuditLogs = async () => (await apiClient.get("/users/audit-logs", { params: { limit: 25 } })).data;
export const createUser = async (user) => (await apiClient.post("/users", user)).data;
export const updateUserStatus = async (id, isActive) => (await apiClient.patch(`/users/${id}/status`, { is_active: isActive })).data;
