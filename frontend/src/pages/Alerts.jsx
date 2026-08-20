import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Search,
  RefreshCw,
  ShieldAlert,
  X,
  MapPin,
  Server,
  Network,
  Fingerprint,
  Crosshair,
} from "lucide-react";

import {
  acknowledgeAlert,
  getAlerts,
  investigateAlert,
  resolveAlert,
} from "../api/alertsApi";

import FilterSelect from "../components/common/FilterSelect";
import Pagination from "../components/common/Pagination";

const severityOptions = [
  { value: "", label: "All severities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
  { value: "info", label: "Info" },
];

const statusOptions = [
  { value: "", label: "All statuses" },
  { value: "open", label: "Open" },
  {
    value: "acknowledged",
    label: "Acknowledged",
  },
  {
    value: "investigating",
    label: "Investigating",
  },
  { value: "resolved", label: "Resolved" },
  {
    value: "false_positive",
    label: "False positive",
  },
];

const providerOptions = [
  { value: "", label: "All providers" },
  { value: "aws", label: "AWS" },
  { value: "azure", label: "Azure" },
  { value: "gcp", label: "GCP" },
];

function formatDate(value) {
  if (!value) return "Unknown";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function shortId(value) {
  if (!value) return "—";

  if (value.length <= 16) {
    return value;
  }

  return `${value.slice(0, 8)}…${value.slice(-5)}`;
}

function Alerts() {
  const [alerts, setAlerts] = useState([]);

  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);

  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [provider, setProvider] = useState("");
  const [accountId, setAccountId] = useState("");

  const [search, setSearch] = useState("");
  const [service, setService] = useState("");
  const [mitre, setMitre] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedAlert, setSelectedAlert] =
    useState(null);

  const [actionLoading, setActionLoading] =
    useState(false);

  const loadAlerts = useCallback(async function loadAlerts() {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        page_size: 25,
        sort_by: "created_at",
        sort_order: "desc",
      };

      if (severity) {
        params.severity = severity;
      }

      if (status) {
        params.status = status;
      }

      if (provider) {
        params.cloud_provider = provider;
      }

      if (accountId.trim()) {
        params.account_id =
          accountId.trim();
      }

      const response =
        await getAlerts(params);

      setAlerts(response.items || []);
      setTotal(response.total || 0);
      setPages(response.pages || 0);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load alerts."
      );
    } finally {
      setLoading(false);
    }
  }, [page, severity, status, provider, accountId]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadAlerts();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadAlerts]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setPage(1);
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [
    severity,
    status,
    provider,
    accountId,
  ]);

  const serviceOptions = useMemo(() => {
    const values = [
      ...new Set(
        alerts
          .map((alert) => alert.service)
          .filter(Boolean)
      ),
    ].sort();

    return [
      {
        value: "",
        label: "All services",
      },

      ...values.map((value) => ({
        value,
        label: value.toUpperCase(),
      })),
    ];
  }, [alerts]);

  const mitreOptions = useMemo(() => {
    const values = [
      ...new Set(
        alerts
          .map(
            (alert) =>
              alert.mitre_tactic
          )
          .filter(Boolean)
      ),
    ].sort();

    return [
      {
        value: "",
        label: "All MITRE tactics",
      },

      ...values.map((value) => ({
        value,
        label: value,
      })),
    ];
  }, [alerts]);

  const visibleAlerts = useMemo(() => {
    const term =
      search.trim().toLowerCase();

    return alerts.filter((alert) => {
      if (
        service &&
        alert.service !== service
      ) {
        return false;
      }

      if (
        mitre &&
        alert.mitre_tactic !== mitre
      ) {
        return false;
      }

      if (!term) {
        return true;
      }

      const searchable = [
        alert.rule_name,
        alert.rule_id,
        alert.description,
        alert.event_name,
        alert.service,
        alert.region,
        alert.source_ip,
        alert.account_id,
        alert.user_identity,
        alert.mitre_tactic,
        alert.mitre_technique,
        alert.mitre_technique_id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchable.includes(term);
    });
  }, [
    alerts,
    search,
    service,
    mitre,
  ]);

  async function performAction(action) {
    if (!selectedAlert) return;

    try {
      setActionLoading(true);

      if (action === "acknowledge") {
        await acknowledgeAlert(
          selectedAlert.alert_id
        );
      }

      if (action === "investigate") {
        await investigateAlert(
          selectedAlert.alert_id
        );
      }

      if (action === "resolve") {
        await resolveAlert(
          selectedAlert.alert_id
        );
      }

      setSelectedAlert(null);

      await loadAlerts();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to update alert."
      );
    } finally {
      setActionLoading(false);
    }
  }

  function resetFilters() {
    setSeverity("");
    setStatus("");
    setProvider("");
    setAccountId("");
    setSearch("");
    setService("");
    setMitre("");
    setPage(1);
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            SECURITY OPERATIONS CENTER
          </p>

          <h1>Security Alerts</h1>

          <p className="page-description">
            Analyze detections generated by the
            cloud security detection engine.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={loadAlerts}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={
              loading ? "spin" : ""
            }
          />

          Refresh
        </button>
      </div>

      <section className="alerts-toolbar panel">
        <div className="alerts-search">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            placeholder="Search rule, event, source IP, MITRE technique..."
          />
        </div>

        <div className="alerts-filters">
          <FilterSelect
            label="Severity"
            value={severity}
            onChange={setSeverity}
            options={severityOptions}
          />

          <FilterSelect
            label="Status"
            value={status}
            onChange={setStatus}
            options={statusOptions}
          />

          <FilterSelect
            label="Provider"
            value={provider}
            onChange={setProvider}
            options={providerOptions}
          />

          <FilterSelect
            label="Service"
            value={service}
            onChange={setService}
            options={serviceOptions}
          />

          <FilterSelect
            label="MITRE"
            value={mitre}
            onChange={setMitre}
            options={mitreOptions}
          />

          <label className="filter-select account-filter">
            <span>Account</span>

            <input
              value={accountId}
              onChange={(event) =>
                setAccountId(
                  event.target.value
                )
              }
              placeholder="Account ID"
            />
          </label>

          <button
            className="clear-filters"
            onClick={resetFilters}
          >
            <X size={14} />
            Clear
          </button>
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
            <h3>
              Detection Queue
            </h3>

            <span>
              Showing {visibleAlerts.length}
              {" "}of {total} matching alerts
            </span>
          </div>

          <div className="live-indicator">
            <span></span>
            LIVE
          </div>
        </div>

        {loading ? (
          <div className="alerts-empty">
            Loading security alerts...
          </div>
        ) : visibleAlerts.length === 0 ? (
          <div className="alerts-empty">
            <ShieldAlert size={34} />

            <strong>
              No alerts match these filters
            </strong>

            <span>
              Change your filter criteria
              or refresh the telemetry.
            </span>
          </div>
        ) : (
          <div className="alerts-table-wrapper">
            <table className="alerts-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Detection</th>
                  <th>Event</th>
                  <th>Service</th>
                  <th>MITRE</th>
                  <th>Source IP</th>
                  <th>Region</th>
                  <th>Status</th>
                  <th>Detected</th>
                </tr>
              </thead>

              <tbody>
                {visibleAlerts.map(
                  (alert) => (
                    <tr
                      key={alert.alert_id}
                      onClick={() =>
                        setSelectedAlert(
                          alert
                        )
                      }
                    >
                      <td>
                        <span
                          className={`severity-badge ${alert.severity}`}
                        >
                          {alert.severity}
                        </span>
                      </td>

                      <td>
                        <div className="detection-cell">
                          <strong>
                            {alert.rule_name}
                          </strong>

                          <span>
                            {alert.rule_id}
                          </span>
                        </div>
                      </td>

                      <td>
                        {alert.event_name}
                      </td>

                      <td>
                        <span className="service-chip">
                          {alert.service ||
                            "—"}
                        </span>
                      </td>

                      <td>
                        <div className="mitre-cell">
                          <strong>
                            {alert.mitre_tactic ||
                              "—"}
                          </strong>

                          <span>
                            {alert.mitre_technique_id ||
                              ""}
                          </span>
                        </div>
                      </td>

                      <td className="mono-cell">
                        {alert.source_ip ||
                          "—"}
                      </td>

                      <td>
                        {alert.region ||
                          "—"}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${alert.status}`}
                        >
                          {alert.status}
                        </span>
                      </td>

                      <td className="date-cell">
                        {formatDate(
                          alert.created_at
                        )}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          page={page}
          pages={pages}
          total={total}
          onPageChange={setPage}
        />
      </section>

      {selectedAlert && (
        <div
          className="alert-drawer-backdrop"
          onClick={() =>
            setSelectedAlert(null)
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
                  className={`severity-badge ${selectedAlert.severity}`}
                >
                  {selectedAlert.severity}
                </span>

                <h2>
                  {selectedAlert.rule_name}
                </h2>

                <p>
                  {selectedAlert.description}
                </p>
              </div>

              <button
                onClick={() =>
                  setSelectedAlert(null)
                }
              >
                <X size={20} />
              </button>
            </div>

            <div className="alert-details-grid">
              <div>
                <Fingerprint size={16} />
                <span>Rule</span>
                <strong>
                  {selectedAlert.rule_id}
                </strong>
              </div>

              <div>
                <Server size={16} />
                <span>Service</span>
                <strong>
                  {selectedAlert.service ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <MapPin size={16} />
                <span>Region</span>
                <strong>
                  {selectedAlert.region ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <Network size={16} />
                <span>Source IP</span>
                <strong>
                  {selectedAlert.source_ip ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <Crosshair size={16} />
                <span>MITRE tactic</span>
                <strong>
                  {selectedAlert.mitre_tactic ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <ShieldAlert size={16} />
                <span>Technique</span>
                <strong>
                  {selectedAlert.mitre_technique ||
                    "Unknown"}
                </strong>
              </div>
            </div>

            <div className="alert-detail-section">
              <span>Alert ID</span>

              <code>
                {selectedAlert.alert_id}
              </code>
            </div>

            <div className="alert-detail-section">
              <span>Event</span>

              <strong>
                {selectedAlert.event_name}
              </strong>

              <small>
                {shortId(
                  selectedAlert.event_id
                )}
              </small>
            </div>

            <div className="alert-detail-section">
              <span>Account</span>

              <strong>
                {selectedAlert.account_id ||
                  "Unknown"}
              </strong>
            </div>

            <div className="alert-detail-section">
              <span>Detected</span>

              <strong>
                {formatDate(
                  selectedAlert.created_at
                )}
              </strong>
            </div>

            <div className="alert-drawer-actions">
              <button
                disabled={actionLoading}
                onClick={() =>
                  performAction(
                    "acknowledge"
                  )
                }
              >
                Acknowledge
              </button>

              <button
                disabled={actionLoading}
                onClick={() =>
                  performAction(
                    "investigate"
                  )
                }
              >
                Investigate
              </button>

              <button
                className="resolve-button"
                disabled={actionLoading}
                onClick={() =>
                  performAction("resolve")
                }
              >
                Resolve
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

export default Alerts;
