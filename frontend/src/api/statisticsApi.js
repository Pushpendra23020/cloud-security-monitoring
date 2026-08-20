import apiClient from "./client";

export async function getStatistics() {
  const response = await apiClient.get("/statistics");
  return response.data;
}
