import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  ShieldAlert,
  RefreshCw,
  X,
  Server,
  Clock,
  Link2,
} from "lucide-react";

import {
  getIncidents,
  getIncidentAlerts,
} from "../api/incidentsApi";

function formatDate(value) {
  if (!value) return "Unknown";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedIncident, setSelectedIncident] =
    useState(null);

  const [linkedAlerts, setLinkedAlerts] =
    useState([]);

  const [alertsLoading, setAlertsLoading] =
    useState(false);

  const loadIncidents = useCallback(async function loadIncidents() {
    try {
      setLoading(true);
      setError(null);

      const response = await getIncidents();

      setIncidents(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load incidents."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadIncidents();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadIncidents]);

  async function openIncident(incident) {
    setSelectedIncident(incident);
    setLinkedAlerts([]);

    try {
      setAlertsLoading(true);

      const response =
        await getIncidentAlerts(
          incident.incident_id ||
          incident.id
        );

      setLinkedAlerts(
        Array.isArray(response)
          ? response
          : response.items || []
      );
    } catch (err) {
      console.error(err);
    } finally {
      setAlertsLoading(false);
    }
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            SECURITY OPERATIONS CENTER
          </p>

          <h1>Incidents</h1>

          <p className="page-description">
            Investigate correlated security activity
            and manage incident response.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={loadIncidents}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? "spin" : ""}
          />

          Refresh
        </button>
      </div>

      <section className="metrics-grid">
        <div className="metric-card">
          <div className="metric-card-header">
            <span>Total Incidents</span>
            <ShieldAlert size={20} />
          </div>

          <div className="metric-value">
            {total}
          </div>

          <div className="metric-change">
            Correlated security cases
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <span>Open</span>
          </div>

          <div className="metric-value">
            {
              incidents.filter(
                (incident) =>
                  incident.status === "open"
              ).length
            }
          </div>

          <div className="metric-change">
            Requires analyst review
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <span>Investigating</span>
          </div>

          <div className="metric-value">
            {
              incidents.filter(
                (incident) =>
                  incident.status ===
                  "investigating"
              ).length
            }
          </div>

          <div className="metric-change">
            Active investigations
          </div>
        </div>

        <div className="metric-card critical">
          <div className="metric-card-header">
            <span>Critical</span>
          </div>

          <div className="metric-value">
            {
              incidents.filter(
                (incident) =>
                  incident.severity ===
                  "critical"
              ).length
            }
          </div>

          <div className="metric-change">
            Highest priority incidents
          </div>
        </div>
      </section>

      {error && (
        <div className="panel alerts-error">
          {String(error)}
        </div>
      )}

      <section className="panel alerts-console">
        <div className="alerts-console-header">
          <div>
            <h3>Incident Queue</h3>

            <span>
              {total} incident
              {total === 1 ? "" : "s"}
            </span>
          </div>

          <div className="live-indicator">
            <span></span>
            LIVE
          </div>
        </div>

        {loading ? (
          <div className="alerts-empty">
            Loading incidents...
          </div>
        ) : incidents.length === 0 ? (
          <div className="alerts-empty">
            <ShieldAlert size={36} />

            <strong>
              No incidents currently available
            </strong>

            <span>
              Correlated detections will appear
              here when promoted to incidents.
            </span>
          </div>
        ) : (
          <div className="alerts-table-wrapper">
            <table className="alerts-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Incident</th>
                  <th>Status</th>
                  <th>Provider</th>
                  <th>Account</th>
                  <th>Created</th>
                </tr>
              </thead>

              <tbody>
                {incidents.map(
                  (incident, index) => (
                    <tr
                      key={
                        incident.incident_id ||
                        incident.id ||
                        index
                      }
                      onClick={() =>
                        openIncident(
                          incident
                        )
                      }
                    >
                      <td>
                        <span
                          className={`severity-badge ${
                            incident.severity ||
                            "unknown"
                          }`}
                        >
                          {incident.severity ||
                            "unknown"}
                        </span>
                      </td>

                      <td>
                        <div className="detection-cell">
                          <strong>
                            {incident.title ||
                              incident.name ||
                              "Security Incident"}
                          </strong>

                          <span>
                            {incident.incident_id ||
                              incident.id ||
                              "—"}
                          </span>
                        </div>
                      </td>

                      <td>
                        <span
                          className={`status-badge ${
                            incident.status ||
                            "open"
                          }`}
                        >
                          {incident.status ||
                            "open"}
                        </span>
                      </td>

                      <td>
                        {incident.cloud_provider ||
                          incident.provider ||
                          "—"}
                      </td>

                      <td className="mono-cell">
                        {incident.account_id ||
                          "—"}
                      </td>

                      <td className="date-cell">
                        {formatDate(
                          incident.created_at
                        )}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedIncident && (
        <div
          className="alert-drawer-backdrop"
          onClick={() =>
            setSelectedIncident(null)
          }
        >
          <aside
            className="alert-drawer"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="alert-drawer-header">
              <div>
                <span
                  className={`severity-badge ${
                    selectedIncident.severity ||
                    "unknown"
                  }`}
                >
                  {selectedIncident.severity ||
                    "unknown"}
                </span>

                <h2>
                  {selectedIncident.title ||
                    selectedIncident.name ||
                    "Security Incident"}
                </h2>

                <p>
                  {selectedIncident.description ||
                    "Correlated security activity requiring investigation."}
                </p>
              </div>

              <button
                onClick={() =>
                  setSelectedIncident(null)
                }
              >
                <X size={20} />
              </button>
            </div>

            <div className="alert-details-grid">
              <div>
                <ShieldAlert size={16} />
                <span>Status</span>
                <strong>
                  {selectedIncident.status ||
                    "open"}
                </strong>
              </div>

              <div>
                <Server size={16} />
                <span>Provider</span>
                <strong>
                  {selectedIncident.cloud_provider ||
                    selectedIncident.provider ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <Clock size={16} />
                <span>Created</span>
                <strong>
                  {formatDate(
                    selectedIncident.created_at
                  )}
                </strong>
              </div>

              <div>
                <Link2 size={16} />
                <span>Linked alerts</span>
                <strong>
                  {alertsLoading
                    ? "Loading..."
                    : linkedAlerts.length}
                </strong>
              </div>
            </div>

            <div className="alert-detail-section">
              <span>Incident ID</span>

              <code>
                {selectedIncident.incident_id ||
                  selectedIncident.id}
              </code>
            </div>

            <div className="alert-detail-section">
              <span>Account</span>

              <strong>
                {selectedIncident.account_id ||
                  "Unknown"}
              </strong>
            </div>

            <div className="alert-detail-section">
              <span>Linked alerts</span>

              {alertsLoading ? (
                <small>
                  Loading related detections...
                </small>
              ) : linkedAlerts.length === 0 ? (
                <small>
                  No linked alerts returned.
                </small>
              ) : (
                linkedAlerts.map(
                  (alert, index) => (
                    <div
                      className="linked-alert"
                      key={
                        alert.alert_id ||
                        index
                      }
                    >
                      <span
                        className={`severity-badge ${
                          alert.severity ||
                          "unknown"
                        }`}
                      >
                        {alert.severity ||
                          "unknown"}
                      </span>

                      <div>
                        <strong>
                          {alert.rule_name ||
                            "Security Alert"}
                        </strong>

                        <small>
                          {alert.event_name ||
                            alert.alert_id}
                        </small>
                      </div>
                    </div>
                  )
                )
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

export default Incidents;
