import apiClient from "./client";

export const listCloudAccounts = async () => (await apiClient.get("/cloud-accounts")).data;
export const createCloudAccount = async (payload) => (await apiClient.post("/cloud-accounts", payload)).data;
export const updateCloudAccount = async (id, payload) => (await apiClient.patch(`/cloud-accounts/${id}`, payload)).data;
export const deleteCloudAccount = async (id) => apiClient.delete(`/cloud-accounts/${id}`);
export const testCloudAccount = async (id) => (await apiClient.post(`/cloud-accounts/${id}/test-connection`)).data;
