import { useCallback, useEffect, useState } from "react";
import {
  Archive,
  CheckCircle2,
  Clock3,
  Inbox,
  RefreshCw,
  RotateCcw,
  TriangleAlert,
} from "lucide-react";

import {
  getDeadLetterEvents,
  getEventQueueStatus,
  replayDeadLetterEvent,
} from "../api/eventQueueApi";
import { useAuth } from "../context/authState";


function formatDate(value) {
  if (!value) return "Not archived";
  return new Date(value).toLocaleString();
}


function formatAge(seconds) {
  if (!seconds) return "No pending events";
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}


export default function EventQueue() {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [deadLetters, setDeadLetters] = useState([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replaying, setReplaying] = useState(null);

  const canReplay = user?.role === "admin" || user?.role === "analyst";

  const loadQueue = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [queueStatus, deadLetterPage] = await Promise.all([
        getEventQueueStatus(),
        getDeadLetterEvents({ page, page_size: 25 }),
      ]);
      setStatus(queueStatus);
      setDeadLetters(deadLetterPage.items || []);
      setPages(deadLetterPage.pages || 0);
      setTotal(deadLetterPage.total || 0);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load event queue health."
      );
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    const initialLoad = window.setTimeout(loadQueue, 0);
    const interval = window.setInterval(loadQueue, 15000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [loadQueue]);

  async function replay(recordId) {
    try {
      setReplaying(recordId);
      setError(null);
      await replayDeadLetterEvent(recordId);
      await loadQueue();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to replay the failed event."
      );
    } finally {
      setReplaying(null);
    }
  }

  const metrics = [
    { label: "Queued", value: status?.queued || 0, icon: Inbox },
    { label: "Processing", value: status?.processing || 0, icon: RefreshCw },
    { label: "Retrying", value: status?.retry || 0, icon: Clock3 },
    { label: "Dead letter", value: status?.dead_letter || 0, icon: TriangleAlert, danger: true },
  ];

  return (
    <div>
      <div className="page-heading">
        <div>
          <p className="eyebrow">INGESTION OPERATIONS</p>
          <h1>Event Queue</h1>
          <p className="page-description">
            Monitor durable ingestion, archive health and failed event recovery.
          </p>
        </div>
        <button className="refresh-button" onClick={loadQueue} disabled={loading}>
          <RefreshCw size={15} className={loading ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {error && <div className="panel queue-error">{String(error)}</div>}

      <section className={`panel queue-health ${status?.healthy ? "healthy" : "degraded"}`}>
        {status?.healthy ? <CheckCircle2 size={22} /> : <TriangleAlert size={22} />}
        <div>
          <strong>{status?.healthy ? "Ingestion is healthy" : "Ingestion needs attention"}</strong>
          <span>Oldest pending event: {formatAge(status?.oldest_pending_age_seconds)}</span>
        </div>
      </section>

      <section className="queue-metrics">
        {metrics.map(({ label, value, icon: Icon, danger }) => (
          <article className={`metric-card queue-metric ${danger && value ? "critical" : ""}`} key={label}>
            <div className="metric-card-header"><span>{label}</span><Icon size={18} className="metric-icon" /></div>
            <div className="metric-value">{value}</div>
          </article>
        ))}
      </section>

      <section className="panel queue-console">
        <div className="queue-console-header">
          <div>
            <h3>Dead-letter events</h3>
            <span>{total} events require operator review</span>
          </div>
          <Archive size={20} />
        </div>

        {loading && !status ? (
          <div className="queue-empty">Loading durable queue state...</div>
        ) : deadLetters.length === 0 ? (
          <div className="queue-empty">
            <CheckCircle2 size={32} />
            <strong>No dead-letter events</strong>
            <span>Failed events will appear here with their archive and retry details.</span>
          </div>
        ) : (
          <div className="alerts-table-wrapper">
            <table className="alerts-table queue-table">
              <thead><tr><th>Event</th><th>Source</th><th>Attempts</th><th>Received</th><th>Archive</th><th>Error</th><th>Action</th></tr></thead>
              <tbody>
                {deadLetters.map((record) => (
                  <tr key={record.id}>
                    <td><code>{record.event_id}</code></td>
                    <td>{record.source}</td>
                    <td>{record.attempts} / {record.max_attempts}</td>
                    <td>{formatDate(record.received_at)}</td>
                    <td><span className={`archive-state ${record.archived_at ? "stored" : "missing"}`}>{record.archived_at ? "Archived" : "Missing"}</span></td>
                    <td className="queue-error-cell" title={record.last_error || ""}>{record.last_error || "Unknown worker error"}</td>
                    <td>
                      <button className="queue-replay-button" disabled={!canReplay || replaying === record.id} onClick={() => replay(record.id)}>
                        <RotateCcw size={14} />
                        {replaying === record.id ? "Replaying" : "Replay"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {pages > 1 && (
          <div className="queue-pagination">
            <button disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button>
            <span>Page {page} of {pages}</span>
            <button disabled={page >= pages} onClick={() => setPage((value) => value + 1)}>Next</button>
          </div>
        )}
      </section>
    </div>
  );
}
