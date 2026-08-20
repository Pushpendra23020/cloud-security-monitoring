import apiClient from "./client";

export async function getAssets() {
  const response = await apiClient.get("/assets");
  return response.data;
}

export async function getCloudAccounts() {
  const response = await apiClient.get("/cloud-accounts");
  return response.data;
}
