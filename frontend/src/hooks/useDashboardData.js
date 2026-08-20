import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getDashboardRiskSummary,
  getDashboardSummary,
  getRecentDashboardAlerts,
  getRecentDashboardIncidents,
} from "../api/dashboardApi";
import { getApiHealth } from "../api/healthApi";

const REFRESH_INTERVAL_MS = 30000;

function useDashboardData() {
  const [summary, setSummary] = useState(null);
  const [riskSummary, setRiskSummary] =
    useState(null);

  const [alerts, setAlerts] = useState([]);
  const [alertTotal, setAlertTotal] =
    useState(0);

  const [incidents, setIncidents] =
    useState([]);
  const [incidentTotal, setIncidentTotal] =
    useState(0);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] =
    useState("checking");

  const [lastUpdated, setLastUpdated] =
    useState(null);

  const hasLoadedRef = useRef(false);
  const requestInFlightRef = useRef(false);

  const refresh = useCallback(async () => {
    if (requestInFlightRef.current) {
      return;
    }

    requestInFlightRef.current = true;

    const initialLoad = !hasLoadedRef.current;

    try {
      if (initialLoad) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError(null);

      const results = await Promise.allSettled([
        getApiHealth(),
        getDashboardSummary(),
        getRecentDashboardAlerts(6),
        getRecentDashboardIncidents(6),
        getDashboardRiskSummary(),
      ]);

      const [
        healthResult,
        summaryResult,
        alertsResult,
        incidentsResult,
        riskResult,
      ] = results;

      const dataResults = [
        summaryResult,
        alertsResult,
        incidentsResult,
        riskResult,
      ];

      const failedRequest = dataResults.find(
        (result) => result.status === "rejected"
      );

      if (failedRequest) {
        throw failedRequest.reason;
      }

      setSummary(summaryResult.value);

      setAlerts(
        alertsResult.value?.items || []
      );

      setAlertTotal(
        alertsResult.value?.total || 0
      );

      setIncidents(
        incidentsResult.value?.items || []
      );

      setIncidentTotal(
        incidentsResult.value?.total || 0
      );

      setRiskSummary(
        riskResult.value
      );

      if (
        healthResult.status === "fulfilled" &&
        healthResult.value?.status === "healthy"
      ) {
        setApiStatus("connected");
      } else {
        setApiStatus("degraded");
      }

      setLastUpdated(
        new Date().toISOString()
      );
    } catch (err) {
      console.error(
        "Dashboard API error:",
        err
      );

      setApiStatus("offline");

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load dashboard data."
      );
    } finally {
      hasLoadedRef.current = true;
      requestInFlightRef.current = false;

      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const initialTimer =
      window.setTimeout(() => {
        refresh();
      }, 0);

    const intervalId =
      window.setInterval(() => {
        refresh();
      }, REFRESH_INTERVAL_MS);

    return () => {
      window.clearTimeout(initialTimer);
      window.clearInterval(intervalId);
    };
  }, [refresh]);

  return {
    summary,
    riskSummary,
    incidents,
    incidentTotal,
    alerts,
    alertTotal,
    loading,
    refreshing,
    error,
    apiStatus,
    lastUpdated,
    refresh,
  };
}

export default useDashboardData;
