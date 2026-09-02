import { useEffect, useState } from "react";
import { KeyRound, Laptop, RefreshCw, ShieldCheck } from "lucide-react";
import {
  beginMfaSetup,
  disableMfa,
  enableMfa,
  getMfaStatus,
  listSessions,
  regenerateRecoveryCodes,
  revokeSession,
} from "../api/authApi";
import { useAuth } from "../context/authState";

export default function Settings() {
  const [notifications, setNotifications] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [revokingId, setRevokingId] = useState(null);
  const [mfaStatus, setMfaStatus] = useState(null);
  const [mfaSetup, setMfaSetup] = useState(null);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaPassword, setMfaPassword] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState([]);
  const [mfaBusy, setMfaBusy] = useState(false);
  const [mfaError, setMfaError] = useState("");
  const { enabled: authEnabled } = useAuth();

  const loadSessions = async () => {
    if (!authEnabled) {
      setSessionLoading(false);
      return;
    }
    setSessionError("");
    try {
      setSessions(await listSessions());
    } catch (error) {
      setSessionError(error.response?.data?.detail || "Unable to load active sessions.");
    } finally {
      setSessionLoading(false);
    }
  };

  useEffect(() => {
    if (!authEnabled) return undefined;
    let active = true;
    listSessions()
      .then((items) => {
        if (active) setSessions(items);
      })
      .catch((error) => {
        if (active) {
          setSessionError(error.response?.data?.detail || "Unable to load active sessions.");
        }
      })
      .finally(() => {
        if (active) setSessionLoading(false);
      });
    return () => {
      active = false;
    };
  }, [authEnabled]);

  useEffect(() => {
    if (!authEnabled) return undefined;
    let active = true;
    getMfaStatus()
      .then((status) => {
        if (active) setMfaStatus(status);
      })
      .catch((error) => {
        if (active) setMfaError(error.response?.data?.detail || "Unable to load MFA status.");
      });
    return () => {
      active = false;
    };
  }, [authEnabled]);

  const revoke = async (sessionId) => {
    setRevokingId(sessionId);
    setSessionError("");
    try {
      await revokeSession(sessionId);
      setSessions((current) => current.filter((session) => session.id !== sessionId));
    } catch (error) {
      setSessionError(error.response?.data?.detail || "Unable to revoke session.");
    } finally {
      setRevokingId(null);
    }
  };

  const startMfa = async () => {
    setMfaBusy(true);
    setMfaError("");
    try {
      setMfaSetup(await beginMfaSetup());
    } catch (error) {
      setMfaError(error.response?.data?.detail || "Unable to start MFA setup.");
    } finally {
      setMfaBusy(false);
    }
  };

  const confirmMfa = async () => {
    setMfaBusy(true);
    setMfaError("");
    try {
      const result = await enableMfa(mfaCode);
      setRecoveryCodes(result.recovery_codes);
      setMfaStatus({ enabled: true, recovery_codes_remaining: result.recovery_codes.length });
      setMfaSetup(null);
      setMfaCode("");
    } catch (error) {
      setMfaError(error.response?.data?.detail || "Unable to enable MFA.");
    } finally {
      setMfaBusy(false);
    }
  };

  const createNewRecoveryCodes = async () => {
    setMfaBusy(true);
    setMfaError("");
    try {
      const result = await regenerateRecoveryCodes(mfaCode);
      setRecoveryCodes(result.recovery_codes);
      setMfaStatus({ enabled: true, recovery_codes_remaining: result.recovery_codes.length });
      setMfaCode("");
    } catch (error) {
      setMfaError(error.response?.data?.detail || "Unable to regenerate recovery codes.");
    } finally {
      setMfaBusy(false);
    }
  };

  const turnOffMfa = async () => {
    setMfaBusy(true);
    setMfaError("");
    try {
      await disableMfa(mfaPassword, mfaCode);
      setMfaStatus({ enabled: false, recovery_codes_remaining: 0 });
      setMfaPassword("");
      setMfaCode("");
      setRecoveryCodes([]);
    } catch (error) {
      setMfaError(error.response?.data?.detail || "Unable to disable MFA.");
    } finally {
      setMfaBusy(false);
    }
  };

  return <div>
    <div className="page-heading"><div><p className="eyebrow">CONFIGURATION</p><h1>Settings</h1><p>Manage your production workspace preferences.</p></div></div>
    <div className="panel settings-panel">
      <h3>Notifications</h3>
      <label className="setting-row"><div><strong>Security alert notifications</strong><small>Show notifications for critical and high-severity detections.</small></div><input type="checkbox" checked={notifications} onChange={(event) => setNotifications(event.target.checked)} /></label>
      <h3>AWS environment</h3>
      <div className="setting-row"><div><strong>Production</strong><small>Account 334767236854 · CloudTrail monitoring enabled</small></div><span className="connected-label">● Connected</span></div>
      {authEnabled && <>
        <div className="settings-section-heading">
          <div><h3>Multi-factor authentication</h3><p>Protect your account with an authenticator app and one-time recovery codes.</p></div>
          {mfaStatus?.enabled ? <span className="current-session-label"><ShieldCheck size={14} /> Enabled</span> : <button className="secondary-button compact-button" type="button" onClick={startMfa} disabled={mfaBusy}><KeyRound size={14} /> Set up MFA</button>}
        </div>
        {mfaError && <div className="inline-error" role="alert">{mfaError}</div>}
        {mfaSetup && <div className="mfa-setup-card">
          <strong>Add Cloud Sentinel to your authenticator</strong>
          <p>Enter this setup key manually, then confirm the six-digit code.</p>
          <code>{mfaSetup.secret}</code>
          <label>Authentication code<input inputMode="numeric" autoComplete="one-time-code" value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} placeholder="123456" /></label>
          <button className="secondary-button" type="button" onClick={confirmMfa} disabled={mfaBusy || mfaCode.length < 6}>Enable MFA</button>
        </div>}
        {mfaStatus?.enabled && <div className="mfa-manage-card">
          <p><strong>{mfaStatus.recovery_codes_remaining}</strong> unused recovery codes remain.</p>
          <label>Current authentication or recovery code<input value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} /></label>
          <div className="mfa-actions"><button className="secondary-button" type="button" onClick={createNewRecoveryCodes} disabled={mfaBusy || mfaCode.length < 6}>Generate new recovery codes</button></div>
          <label>Current password<input type="password" autoComplete="current-password" value={mfaPassword} onChange={(event) => setMfaPassword(event.target.value)} /></label>
          <button className="danger-outline-button" type="button" onClick={turnOffMfa} disabled={mfaBusy || !mfaPassword || mfaCode.length < 6}>Disable MFA</button>
        </div>}
        {recoveryCodes.length > 0 && <div className="recovery-code-card" role="status">
          <strong>Save these recovery codes now</strong><p>Each code works once. They will not be shown again.</p>
          <div className="recovery-code-grid">{recoveryCodes.map((code) => <code key={code}>{code}</code>)}</div>
        </div>}
        <div className="settings-section-heading">
          <div><h3>Active sessions</h3><p>Review browsers signed in to your account and revoke access you do not recognize.</p></div>
          <button className="secondary-button compact-button" type="button" onClick={loadSessions} disabled={sessionLoading}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
        {sessionLoading ? <div className="session-empty">Loading sessions…</div> : sessionError ? <div className="inline-error" role="alert">{sessionError}</div> : sessions.length === 0 ? <div className="session-empty">No active sessions.</div> : <div className="session-list">
          {sessions.map((session) => <div className="session-row" key={session.id}>
            <div className="session-device"><Laptop size={19} /><div><strong>{session.user_agent || "Unknown browser"}</strong><small>{session.client_ip || "Unknown address"} · Last active {new Date(session.last_seen_at).toLocaleString()}</small></div></div>
            {session.is_current ? <span className="current-session-label"><ShieldCheck size={14} /> Current session</span> : <button className="danger-outline-button" type="button" disabled={revokingId === session.id} onClick={() => revoke(session.id)}>{revokingId === session.id ? "Revoking…" : "Revoke"}</button>}
          </div>)}
        </div>}
      </>}
    </div>
  </div>;
}
