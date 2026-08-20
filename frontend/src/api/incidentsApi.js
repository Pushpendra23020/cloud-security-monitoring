import apiClient from "./client";

export async function getIncidents(params = {}) {
  const response = await apiClient.get("/incidents", {
    params,
  });

  return response.data;
}

export async function getIncident(incidentId) {
  const response = await apiClient.get(
    `/incidents/${incidentId}`
  );

  return response.data;
}

export async function getIncidentAlerts(incidentId) {
  const response = await apiClient.get(
    `/incidents/${incidentId}/alerts`
  );

  return response.data;
}
