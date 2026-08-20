import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Server,
  MapPin,
  RefreshCw,
  Search,
  X,
  Clock,
  ShieldAlert,
  AlertTriangle,
  Globe2,
  Lock,
  Activity,
  Tags,
} from "lucide-react";

import {
  getAssets,
  getCloudAccounts,
} from "../api/assetsApi";

function formatDate(value) {
  if (!value) return "Never";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatAssetType(value) {
  if (!value) return "Unknown";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );
}

function Assets() {
  const [assets, setAssets] = useState([]);
  const [accounts, setAccounts] = useState([]);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] =
    useState("");
  const [regionFilter, setRegionFilter] =
    useState("");
  const [riskFilter, setRiskFilter] =
    useState("");

  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState(null);

  const [selectedAsset, setSelectedAsset] =
    useState(null);

  const loadAssets = useCallback(async function loadAssets() {
    try {
      setLoading(true);
      setError(null);

      const [assetResponse, accountResponse] =
        await Promise.all([
          getAssets(),
          getCloudAccounts(),
        ]);

      setAssets(
        Array.isArray(assetResponse)
          ? assetResponse
          : []
      );

      setAccounts(
        Array.isArray(accountResponse)
          ? accountResponse
          : []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load cloud assets."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadAssets();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadAssets]);

  const accountMap = useMemo(() => {
    return Object.fromEntries(
      accounts.map((account) => [
        account.id,
        account,
      ])
    );
  }, [accounts]);

  const assetTypes = useMemo(() => {
    return [
      ...new Set(
        assets
          .map((asset) => asset.asset_type)
          .filter(Boolean)
      ),
    ].sort();
  }, [assets]);

  const regions = useMemo(() => {
    return [
      ...new Set(
        assets
          .map((asset) => asset.region)
          .filter(Boolean)
      ),
    ].sort();
  }, [assets]);

  const visibleAssets = useMemo(() => {
    const term =
      search.trim().toLowerCase();

    return assets.filter((asset) => {
      if (
        typeFilter &&
        asset.asset_type !== typeFilter
      ) {
        return false;
      }

      if (
        regionFilter &&
        asset.region !== regionFilter
      ) {
        return false;
      }

      if (
        riskFilter &&
        asset.risk_level !== riskFilter
      ) {
        return false;
      }

      if (!term) return true;

      const account =
        accountMap[asset.cloud_account_id];

      const searchable = [
        asset.name,
        asset.asset_id,
        asset.asset_type,
        asset.region,
        asset.risk_level,
        asset.resource_state,
        account?.provider,
        account?.account_id,
        ...Object.entries(
          asset.tags || {}
        ).flat(),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchable.includes(term);
    });
  }, [
    assets,
    search,
    typeFilter,
    regionFilter,
    riskFilter,
    accountMap,
  ]);

  const criticalAssets =
    assets.filter(
      (asset) =>
        asset.risk_level === "critical"
    ).length;

  const exposedAssets =
    assets.filter(
      (asset) => asset.public_exposure
    ).length;

  const totalFindings =
    assets.reduce(
      (sum, asset) =>
        sum + (asset.findings_count || 0),
      0
    );

  return (
    <div>
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            CLOUD SECURITY INVENTORY
          </p>

          <h1>Cloud Assets</h1>

          <p className="page-description">
            Inventory, exposure and risk context
            across connected cloud resources.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={loadAssets}
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
            <span>Total Assets</span>
            <Server size={19} />
          </div>

          <div className="metric-value">
            {assets.length}
          </div>

          <div className="metric-change">
            Discovered resources
          </div>
        </div>

        <div className="metric-card critical">
          <div className="metric-card-header">
            <span>Critical Assets</span>
            <ShieldAlert size={19} />
          </div>

          <div className="metric-value">
            {criticalAssets}
          </div>

          <div className="metric-change">
            Highest risk resources
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <span>Public Exposure</span>
            <Globe2 size={19} />
          </div>

          <div className="metric-value">
            {exposedAssets}
          </div>

          <div className="metric-change">
            Internet-exposed resources
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <span>Findings</span>
            <AlertTriangle size={19} />
          </div>

          <div className="metric-value">
            {totalFindings}
          </div>

          <div className="metric-change">
            Security findings
          </div>
        </div>
      </section>

      <section className="panel assets-toolbar">
        <div className="alerts-search">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search resource ID, name, region, tags, account..."
          />
        </div>

        <div className="alerts-filters">
          <label className="filter-select">
            <span>Asset Type</span>

            <select
              value={typeFilter}
              onChange={(event) =>
                setTypeFilter(
                  event.target.value
                )
              }
            >
              <option value="">
                All asset types
              </option>

              {assetTypes.map((value) => (
                <option
                  key={value}
                  value={value}
                >
                  {formatAssetType(value)}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-select">
            <span>Region</span>

            <select
              value={regionFilter}
              onChange={(event) =>
                setRegionFilter(
                  event.target.value
                )
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
          </label>

          <label className="filter-select">
            <span>Risk</span>

            <select
              value={riskFilter}
              onChange={(event) =>
                setRiskFilter(
                  event.target.value
                )
              }
            >
              <option value="">
                All risk levels
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
          </label>

          <button
            className="clear-filters"
            onClick={() => {
              setSearch("");
              setTypeFilter("");
              setRegionFilter("");
              setRiskFilter("");
            }}
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
            <h3>Asset Risk Inventory</h3>

            <span>
              Showing {visibleAssets.length}
              {" "}of {assets.length} assets
            </span>
          </div>

          <div className="live-indicator">
            <span></span>
            INVENTORY
          </div>
        </div>

        {loading ? (
          <div className="alerts-empty">
            Loading cloud assets...
          </div>
        ) : visibleAssets.length === 0 ? (
          <div className="alerts-empty">
            <Server size={36} />

            <strong>
              No assets match the filters
            </strong>
          </div>
        ) : (
          <div className="alerts-table-wrapper">
            <table className="alerts-table">
              <thead>
                <tr>
                  <th>Risk</th>
                  <th>Asset</th>
                  <th>Type</th>
                  <th>State</th>
                  <th>Exposure</th>
                  <th>Findings</th>
                  <th>Alerts</th>
                  <th>Region</th>
                  <th>Last Seen</th>
                </tr>
              </thead>

              <tbody>
                {visibleAssets.map(
                  (asset) => (
                    <tr
                      key={asset.id}
                      onClick={() =>
                        setSelectedAsset(
                          asset
                        )
                      }
                    >
                      <td>
                        <div className="risk-cell">
                          <span
                            className={`severity-badge ${
                              asset.risk_level ||
                              "low"
                            }`}
                          >
                            {asset.risk_level ||
                              "low"}
                          </span>

                          <strong>
                            {asset.risk_score ?? 0}
                          </strong>
                        </div>
                      </td>

                      <td>
                        <div className="detection-cell">
                          <strong>
                            {asset.name ||
                              "Unnamed Asset"}
                          </strong>

                          <span>
                            {asset.asset_id}
                          </span>
                        </div>
                      </td>

                      <td>
                        <span className="service-chip">
                          {formatAssetType(
                            asset.asset_type
                          )}
                        </span>
                      </td>

                      <td>
                        <span className="asset-state">
                          <Activity size={12} />
                          {asset.resource_state ||
                            "unknown"}
                        </span>
                      </td>

                      <td>
                        {asset.public_exposure ? (
                          <span className="exposure-public">
                            <Globe2 size={12} />
                            PUBLIC
                          </span>
                        ) : (
                          <span className="exposure-private">
                            <Lock size={12} />
                            PRIVATE
                          </span>
                        )}
                      </td>

                      <td>
                        {asset.findings_count ?? 0}
                      </td>

                      <td>
                        {asset.alerts_count ?? 0}
                      </td>

                      <td>
                        {asset.region || "—"}
                      </td>

                      <td className="date-cell">
                        {formatDate(
                          asset.last_seen
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

      {selectedAsset && (
        <div
          className="alert-drawer-backdrop"
          onClick={() =>
            setSelectedAsset(null)
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
                    selectedAsset.risk_level ||
                    "low"
                  }`}
                >
                  {selectedAsset.risk_level ||
                    "low"}
                </span>

                <h2>
                  {selectedAsset.name ||
                    selectedAsset.asset_id}
                </h2>

                <p>
                  Security posture and cloud
                  inventory context.
                </p>
              </div>

              <button
                onClick={() =>
                  setSelectedAsset(null)
                }
              >
                <X size={20} />
              </button>
            </div>

            <div className="asset-risk-score">
              <span>RISK SCORE</span>

              <strong>
                {selectedAsset.risk_score ?? 0}
              </strong>

              <small>/ 100</small>
            </div>

            <div className="alert-details-grid">
              <div>
                <AlertTriangle size={16} />
                <span>Findings</span>
                <strong>
                  {selectedAsset.findings_count ??
                    0}
                </strong>
              </div>

              <div>
                <ShieldAlert size={16} />
                <span>Alerts</span>
                <strong>
                  {selectedAsset.alerts_count ??
                    0}
                </strong>
              </div>

              <div>
                <Globe2 size={16} />
                <span>Exposure</span>
                <strong>
                  {selectedAsset.public_exposure
                    ? "Public"
                    : "Private"}
                </strong>
              </div>

              <div>
                <Activity size={16} />
                <span>State</span>
                <strong>
                  {selectedAsset.resource_state ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <MapPin size={16} />
                <span>Region</span>
                <strong>
                  {selectedAsset.region ||
                    "Unknown"}
                </strong>
              </div>

              <div>
                <Clock size={16} />
                <span>Last Seen</span>
                <strong>
                  {formatDate(
                    selectedAsset.last_seen
                  )}
                </strong>
              </div>
            </div>

            <div className="alert-detail-section">
              <span>Resource ID</span>
              <code>
                {selectedAsset.asset_id}
              </code>
            </div>

            <div className="alert-detail-section">
              <span>Cloud Account</span>
              <strong>
                {accountMap[
                  selectedAsset.cloud_account_id
                ]?.account_id ||
                  selectedAsset.cloud_account_id}
              </strong>
            </div>

            <div className="alert-detail-section">
              <span>Asset Type</span>
              <strong>
                {formatAssetType(
                  selectedAsset.asset_type
                )}
              </strong>
            </div>

            <div className="alert-detail-section">
              <span>
                <Tags
                  size={12}
                  style={{
                    marginRight: "5px",
                  }}
                />
                Tags
              </span>

              {Object.keys(
                selectedAsset.tags || {}
              ).length === 0 ? (
                <small>
                  No tags available.
                </small>
              ) : (
                <div className="asset-tags">
                  {Object.entries(
                    selectedAsset.tags
                  ).map(
                    ([key, value]) => (
                      <span key={key}>
                        {key}={String(value)}
                      </span>
                    )
                  )}
                </div>
              )}
            </div>

            <div className="alert-detail-section">
              <span>Created</span>

              <strong>
                {formatDate(
                  selectedAsset.created_at
                )}
              </strong>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

export default Assets;
