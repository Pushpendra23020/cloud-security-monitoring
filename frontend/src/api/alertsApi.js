import apiClient from "./client";

export async function getAlerts(params = {}) {
  const response = await apiClient.get("/alerts", {
    params,
  });

  return response.data;
}

export async function getAlert(alertId) {
  const response = await apiClient.get(
    `/alerts/${alertId}`
  );

  return response.data;
}

export async function acknowledgeAlert(alertId) {
  const response = await apiClient.post(
    `/alerts/${alertId}/acknowledge`
  );

  return response.data;
}

export async function investigateAlert(alertId) {
  const response = await apiClient.post(
    `/alerts/${alertId}/investigate`
  );

  return response.data;
}

export async function resolveAlert(alertId) {
  const response = await apiClient.post(
    `/alerts/${alertId}/resolve`
  );

  return response.data;
}
