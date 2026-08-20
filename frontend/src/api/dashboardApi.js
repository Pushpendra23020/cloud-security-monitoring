import apiClient from "./client";

export async function getDashboardSummary() {
  const response = await apiClient.get(
    "/dashboard/summary"
  );

  return response.data;
}

export async function getRecentDashboardAlerts(
  limit = 6
) {
  const response = await apiClient.get(
    "/dashboard/recent-alerts",
    {
      params: {
        limit,
      },
    }
  );

  return response.data;
}

export async function getRecentDashboardIncidents(
  limit = 6
) {
  const response = await apiClient.get(
    "/dashboard/recent-incidents",
    {
      params: {
        limit,
      },
    }
  );

  return response.data;
}

export async function getDashboardRiskSummary() {
  const response = await apiClient.get(
    "/dashboard/risk-summary"
  );

  return response.data;
}
