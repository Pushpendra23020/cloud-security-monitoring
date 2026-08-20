import apiClient from "./client";

export async function getApiHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}
