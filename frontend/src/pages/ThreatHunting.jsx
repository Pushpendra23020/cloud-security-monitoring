import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Crosshair,
  Search,
  RefreshCw,
  Filter,
  ShieldAlert,
  Server,
  Network,
  MapPin,
  Fingerprint,
  User,
} from "lucide-react";

import { getAlerts } from "../api/alertsApi";

function normalize(value) {
  return String(value || "").toLowerCase();
}

function formatDate(value) {
  if (!value) return "Unknown";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function ThreatHunting() {
  const [alerts, setAlerts] = useState([]);

  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("");
  const [service, setService] = useState("");
  const [region, setRegion] = useState("");
  const [mitre, setMitre] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const response = await getAlerts({
        page: 1,
        page_size: 100,
        sort_by: "created_at",
        sort_order: "desc",
      });

      setAlerts(response.items || []);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load threat telemetry."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadData();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadData]);

  const services = useMemo(() => {
    return [
      ...new Set(
        alerts
          .map((alert) => alert.service)
          .filter(Boolean)
      ),
    ].sort();
  }, [alerts]);

  const regions = useMemo(() => {
    return [
      ...new Set(
        alerts
          .map((alert) => alert.region)
          .filter(Boolean)
      ),
    ].sort();
  }, [alerts]);

  const mitreTactics = useMemo(() => {
    return [
      ...new Set(
        alerts
          .map((alert) => alert.mitre_tactic)
          .filter(Boolean)
      ),
    ].sort();
  }, [alerts]);

  const results = useMemo(() => {
    const searchTerm = normalize(query.trim());

    return alerts.filter((alert) => {
      if (
        severity &&
        alert.severity !== severity
      ) {
        return false;
      }

      if (
        service &&
        alert.service !== service
      ) {
        return false;
      }

      if (
        region &&
        alert.region !== region
      ) {
        return false;
      }

      if (
        mitre &&
        alert.mitre_tactic !== mitre
      ) {
        return false;
      }

      if (!searchTerm) {
        return true;
      }

      const values = [
        alert.rule_name,
        alert.rule_id,
        alert.description,
        alert.event_name,
        alert.source_ip,
        alert.service,
        alert.region,
        alert.account_id,
        alert.user_identity,
        alert.mitre_tactic,
        alert.mitre_technique,
        alert.mitre_technique_id,
        alert.cloud_provider,
        alert.status,
      ];

      return values
        .filter(Boolean)
        .map(normalize)
        .some((value) =>
          value.includes(searchTerm)
        );
    });
  }, [
    alerts,
    query,
    severity,
    service,
    region,
    mitre,
  ]);

  const sourceIps = useMemo(() => {
    const counts = {};

    results.forEach((alert) => {
      if (!alert.source_ip) return;

      counts[alert.source_ip] =
        (counts[alert.source_ip] || 0) + 1;
    });

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  }, [results]);

  const tacticCounts = useMemo(() => {
    const counts = {};

    results.forEach((alert) => {
      const tactic =
        alert.mitre_tactic || "Unknown";

      counts[tactic] =
        (counts[tactic] || 0) + 1;
    });

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [results]);

  function clearFilters() {
    setQuery("");
    setSeverity("");
    setService("");
    setRegion("");
    setMitre("");
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            THREAT HUNTING
          </p>

          <h1>Threat Hunting</h1>

          <p className="page-description">
            Search and investigate suspicious
            cloud activity across detections,
            identities, IPs and MITRE techniques.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={loadData}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? "spin" : ""}
          />

          Refresh
        </button>
      </div>

      <section className="panel hunt-query-panel">
        <div className="hunt-search">
          <Search size={18} />

          <input
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="Search IP, event, IAM user, rule, MITRE technique, account..."
          />

          <kbd>HUNT</kbd>
        </div>

        <div className="hunt-filters">
          <select
            value={severity}
            onChange={(event) =>
              setSeverity(event.target.value)
            }
          >
            <option value="">
              All severities
            </option>
            <option value="critical">
              Critical
            </option>
            <option value="high">
              High
            </option>
            <option value="medium">
              Medium
            </option>
            <option value="low">
              Low
            </option>
          </select>

          <select
            value={service}
            onChange={(event) =>
              setService(event.target.value)
            }
          >
            <option value="">
              All services
            </option>

            {services.map((value) => (
              <option
                key={value}
                value={value}
              >
                {value}
              </option>
            ))}
          </select>

          <select
            value={region}
            onChange={(event) =>
              setRegion(event.target.value)
            }
          >
            <option value="">
              All regions
            </option>

            {regions.map((value) => (
              <option
                key={value}
                value={value}
              >
                {value}
              </option>
            ))}
          </select>

          <select
            value={mitre}
            onChange={(event) =>
              setMitre(event.target.value)
            }
          >
            <option value="">
              All MITRE tactics
            </option>

            {mitreTactics.map((value) => (
              <option
                key={value}
                value={value}
              >
                {value}
              </option>
            ))}
          </select>

          <button
            className="clear-filters"
            onClick={clearFilters}
          >
            <Filter size={14} />
            Reset hunt
          </button>
        </div>
      </section>

      {error && (
        <div className="panel alerts-error">
          {String(error)}
        </div>
      )}

      <section className="hunt-summary-grid">
        <div className="metric-card">
          <div className="metric-card-header">
            <span>Matches</span>
            <Crosshair size={19} />
          </div>

          <div className="metric-value">
            {results.length}
          </div>

          <div className="metric-change">
            Matching security detections
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <span>Unique IPs</span>
            <Network size={19} />
          </div>

          <div className="metric-value">
            {
              new Set(
                results
                  .map(
                    (alert) =>
                      alert.source_ip
                  )
                  .filter(Boolean)
              ).size
            }
          </div>

          <div className="metric-change">
            Observed source addresses
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <span>Services</span>
            <Server size={19} />
          </div>

          <div className="metric-value">
            {
              new Set(
                results
                  .map(
                    (alert) =>
                      alert.service
                  )
                  .filter(Boolean)
              ).size
            }
          </div>

          <div className="metric-change">
            Cloud services involved
          </div>
        </div>

        <div className="metric-card critical">
          <div className="metric-card-header">
            <span>Critical</span>
            <ShieldAlert size={19} />
          </div>

          <div className="metric-value">
            {
              results.filter(
                (alert) =>
                  alert.severity ===
                  "critical"
              ).length
            }
          </div>

          <div className="metric-change">
            High-priority hunt results
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>
                Top Source IPs
              </h3>

              <span>
                Most active addresses in
                current hunt results
              </span>
            </div>
          </div>

          <div className="hunt-ranking">
            {sourceIps.length === 0 ? (
              <div className="hunt-empty-small">
                No source IP data
              </div>
            ) : (
              sourceIps.map(
                ([ip, count], index) => (
                  <div
                    className="hunt-ranking-row"
                    key={ip}
                  >
                    <span>
                      #{index + 1}
                    </span>

                    <code>{ip}</code>

                    <strong>
                      {count}
                    </strong>
                  </div>
                )
              )
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>
                MITRE Activity
              </h3>

              <span>
                Tactics represented in
                hunt results
              </span>
            </div>
          </div>

          <div className="hunt-ranking">
            {tacticCounts.length === 0 ? (
              <div className="hunt-empty-small">
                No MITRE activity
              </div>
            ) : (
              tacticCounts.map(
                ([tactic, count]) => (
                  <div
                    className="hunt-ranking-row"
                    key={tactic}
                  >
                    <span>
                      <Fingerprint size={13} />
                    </span>

                    <strong className="hunt-label">
                      {tactic}
                    </strong>

                    <strong>
                      {count}
                    </strong>
                  </div>
                )
              )
            )}
          </div>
        </div>
      </section>

      <section className="panel alerts-console">
        <div className="alerts-console-header">
          <div>
            <h3>
              Hunt Results
            </h3>

            <span>
              {results.length} matching
              detections
            </span>
          </div>

          <div className="live-indicator">
            <span></span>
            TELEMETRY
          </div>
        </div>

        {loading ? (
          <div className="alerts-empty">
            Loading threat telemetry...
          </div>
        ) : results.length === 0 ? (
          <div className="alerts-empty">
            <Crosshair size={36} />

            <strong>
              No matching telemetry
            </strong>

            <span>
              Modify your hunt query or
              filters.
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
                  <th>Identity</th>
                  <th>Source IP</th>
                  <th>Service</th>
                  <th>Region</th>
                  <th>MITRE</th>
                  <th>Time</th>
                </tr>
              </thead>

              <tbody>
                {results.map(
                  (alert) => (
                    <tr
                      key={alert.alert_id}
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
                        <div className="hunt-icon-cell">
                          <User size={12} />

                          <span>
                            {alert.user_identity ||
                              "Unknown"}
                          </span>
                        </div>
                      </td>

                      <td className="mono-cell">
                        {alert.source_ip ||
                          "—"}
                      </td>

                      <td>
                        <span className="service-chip">
                          {alert.service ||
                            "—"}
                        </span>
                      </td>

                      <td>
                        <div className="hunt-icon-cell">
                          <MapPin size={12} />

                          <span>
                            {alert.region ||
                              "—"}
                          </span>
                        </div>
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
      </section>
    </div>
  );
}

export default ThreatHunting;
