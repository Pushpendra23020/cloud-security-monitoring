import {
  Activity,
  Bell,
  ShieldAlert,
  TriangleAlert,
  TrendingUp,
  Clock,
  RefreshCw,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import MetricCard from "../components/dashboard/MetricCard";
import useDashboardData from "../hooks/useDashboardData";

function formatDate(value) {
  if (!value) return "Unknown";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function Dashboard() {
  const navigate = useNavigate();

  const {
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
  } = useDashboardData();
  
  const critical =
    summary?.alerts?.critical ?? 0;

  const high =
    summary?.alerts?.high ?? 0;

  const medium =
    summary?.alerts?.medium ?? 0;

  const low =
    summary?.alerts?.low ?? 0;

  const openAlerts =
    summary?.alerts?.open ?? 0;

  const openIncidents =
    summary?.incidents?.open ?? 0;

  const totalAssets =
    riskSummary?.total_assets ??
    summary?.assets?.total ??
    0;

  const averageRiskScore =
    riskSummary?.average_risk_score ?? 0;

  const publicExposure =
    riskSummary?.public_exposure ?? 0;

  const displayedAlerts =
    alerts.slice(0, 6);

  const severityData = [
    {
      name: "Critical",
      value: critical,
    },
    {
      name: "High",
      value: high,
    },
    {
      name: "Medium",
      value: medium,
    },
    {
      name: "Low",
      value: low,
    },
  ];

  const assetRiskData = [
    {
      name: "Critical",
      value: riskSummary?.critical ?? 0,
    },
    {
      name: "High",
      value: riskSummary?.high ?? 0,
    },
    {
      name: "Medium",
      value: riskSummary?.medium ?? 0,
    },
    {
      name: "Low",
      value: riskSummary?.low ?? 0,
    },
  ];

  const severityChartColors = [
    "var(--critical, #ef4444)",
    "var(--high, #f97316)",
    "var(--medium, #eab308)",
    "var(--low, #22c55e)",
  ];


  return (
    <div>
      {loading && (
        <div className="panel dashboard-message">
          Loading live security telemetry...
        </div>
      )}

      {error && (
        <div className="panel dashboard-message error-message">
          <div>
            <strong>
              Security telemetry unavailable
            </strong>

            <span>
              {String(error)}
            </span>
          </div>

          <button
            type="button"
            className="dashboard-retry-button"
            onClick={refresh}
            disabled={refreshing}
          >
            Retry
          </button>
        </div>
      )}

      <div className="page-heading">
        <div>
          <p className="eyebrow">
            SECURITY OPERATIONS CENTER
          </p>

          <h1>Security Overview</h1>

          <p className="page-description">
            Real-time visibility into cloud threats,
            alerts and incidents.
          </p>
        </div>

        <div className="dashboard-controls">
          <div
            className={`api-health ${apiStatus}`}
          >
            <span className="api-health-dot"></span>

            {apiStatus === "connected"
              ? "API Connected"
              : apiStatus === "degraded"
                ? "API Degraded"
                : apiStatus === "offline"
                  ? "API Offline"
                  : "Checking API"}
          </div>

          <div className="last-updated">
            <Clock size={14} />

            {lastUpdated
              ? `Updated ${new Date(
                  lastUpdated
                ).toLocaleTimeString()}`
              : "Waiting for telemetry"}
          </div>

          <button
            type="button"
            className="dashboard-refresh-button"
            onClick={refresh}
            disabled={refreshing}
          >
            <RefreshCw
              size={16}
              className={
                refreshing ? "spin" : ""
              }
            />

            {refreshing
              ? "Refreshing"
              : "Refresh"}
          </button>
        </div>
      </div>

      <section className="metrics-grid">
        <MetricCard
          title="Detected Alerts"
          value={alertTotal}
          change={`${openAlerts} currently open`}
          icon={Activity}
        />

        <MetricCard
          title="Active Alerts"
          value={openAlerts}
          change={`${high} high severity`}
          icon={Bell}
        />

        <MetricCard
          title="Open Incidents"
          value={openIncidents}
          change={
            openIncidents === 0
              ? "No active incidents"
              : `${openIncidents} require analyst review`
          }
          icon={ShieldAlert}
        />

        <MetricCard
          title="Critical Threats"
          value={critical}
          change={
            critical > 0
              ? "Immediate investigation required"
              : "No critical threats"
          }
          icon={TriangleAlert}
          severity="critical"
        />
      </section>

      <section className="dashboard-grid">
        <div className="panel threat-panel">
          <div className="panel-header">
            <div>
              <h3>Threat Severity</h3>
              <span>
                Live alert severity distribution
              </span>
            </div>

            <TrendingUp size={20} />
          </div>

          <div className="dashboard-chart">
            <ResponsiveContainer
              width="100%"
              height={280}
            >
              <BarChart data={severityData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  opacity={0.2}
                />

                <XAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />

                <Tooltip />

                <Bar
                  dataKey="value"
                  radius={[6, 6, 0, 0]}
                >
                  {severityData.map(
                    (entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={
                          severityChartColors[
                            index
                          ]
                        }
                      />
                    )
                  )}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel severity-panel">
          <div className="panel-header">
            <div>
              <h3>Asset Risk</h3>

              <span>
                Current cloud asset posture
              </span>
            </div>
          </div>

          <div className="asset-risk-layout">
            <div className="asset-risk-chart">
              <ResponsiveContainer
                width="100%"
                height={220}
              >
                <PieChart>
                  <Pie
                    data={assetRiskData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={58}
                    outerRadius={82}
                    paddingAngle={3}
                  >
                    {assetRiskData.map(
                      (entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={
                            severityChartColors[
                              index
                            ]
                          }
                        />
                      )
                    )}
                  </Pie>

                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>

              <div className="asset-risk-center">
                <strong>{totalAssets}</strong>
                <span>Assets</span>
              </div>
            </div>

            <div className="risk-stat-list">
              <div className="risk-stat">
                <span>
                  Average Risk Score
                </span>

                <strong>
                  {averageRiskScore}
                </strong>
              </div>

              <div className="risk-stat">
                <span>
                  Public Exposure
                </span>

                <strong>
                  {publicExposure}
                </strong>
              </div>

              <div className="risk-stat">
                <span>
                  High + Critical
                </span>

                <strong>
                  {(riskSummary?.high ?? 0) +
                    (riskSummary?.critical ?? 0)}
                </strong>
              </div>

              <div className="risk-stat">
                <span>
                  Low Risk
                </span>

                <strong>
                  {riskSummary?.low ?? 0}
                </strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="panel incidents-panel">
        <div className="panel-header incidents-heading">
          <div>
            <h3>
              {incidentTotal > 0
                ? "Active Incidents"
                : "Recent Security Alerts"}
            </h3>

            <span>
              {incidentTotal > 0
                ? "Threats requiring analyst attention"
                : "Latest detections from the security engine"}
            </span>
          </div>

          <button
            type="button"
            className="view-all-button"
            onClick={() =>
              navigate(
                incidentTotal > 0
                  ? "/incidents"
                  : "/alerts"
              )
            }
          >
            {incidentTotal > 0
              ? "View all incidents"
              : "View all alerts"}
          </button>
        </div>

        {incidentTotal > 0 ? (
          <div className="incident-table">
            <div className="incident-row incident-table-header">
              <span>Severity</span>
              <span>Incident</span>
              <span>Source</span>
              <span>Status</span>
              <span>Detected</span>
            </div>

            {incidents.slice(0, 6).map(
              (incident, index) => {
                const severity =
                  incident.severity || "unknown";

                const status =
                  incident.status || "open";

                return (
                  <div
                    className="incident-row"
                    key={
                      incident.incident_id ||
                      incident.id ||
                      index
                    }
                  >
                    <span>
                      <span
                        className={`severity-badge ${String(
                          severity
                        ).toLowerCase()}`}
                      >
                        {severity}
                      </span>
                    </span>

                    <strong>
                      {incident.title ||
                        incident.name ||
                        "Security Incident"}
                    </strong>

                    <span className="muted">
                      {incident.cloud_provider ||
                        incident.source ||
                        "Cloud"}
                    </span>

                    <span>
                      <span
                        className={`status-badge ${String(
                          status
                        ).toLowerCase()}`}
                      >
                        {status}
                      </span>
                    </span>

                    <span className="muted">
                      {formatDate(
                        incident.created_at
                      )}
                    </span>
                  </div>
                );
              }
            )}
          </div>
        ) : (
          <div className="incident-table">
            <div className="incident-row incident-table-header">
              <span>Severity</span>
              <span>Detection</span>
              <span>Service</span>
              <span>Status</span>
              <span>Detected</span>
            </div>

            {displayedAlerts.length === 0 ? (
              <div className="dashboard-empty-state">
                <ShieldAlert size={28} />

                <strong>
                  No recent security alerts
                </strong>

                <span>
                  New detections will appear here
                  automatically.
                </span>
              </div>
            ) : (
              displayedAlerts.map((alert, index) => (
              <div
                className="incident-row"
                key={alert.alert_id || index}
              >
                <span>
                  <span
                    className={`severity-badge ${String(
                      alert.severity || "unknown"
                    ).toLowerCase()}`}
                  >
                    {alert.severity || "unknown"}
                  </span>
                </span>

                <strong>
                  {alert.rule_name ||
                    "Security Detection"}
                </strong>

                <span className="muted">
                  {(
                    alert.cloud_provider ||
                    "Cloud"
                  ).toUpperCase()}
                </span>

                <span>
                  <span
                    className={`status-badge ${String(
                      alert.status || "open"
                    ).toLowerCase()}`}
                  >
                    {alert.status || "open"}
                  </span>
                </span>

                <span className="muted">
                  {formatDate(alert.created_at)}
                </span>
              </div>
            ))
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export default Dashboard;
