import { useEffect, useState } from "react";
import { createUser, listAuditLogs, listUsers, updateUserStatus } from "../api/usersApi";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "analyst" });

  const refresh = async () => {
    try {
      const [userData, logData] = await Promise.all([listUsers(), listAuditLogs()]);
      setUsers(userData); setLogs(logData); setError("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load access management data.");
    }
  };
  useEffect(() => {
    Promise.all([listUsers(), listAuditLogs()])
      .then(([userData, logData]) => {
        setUsers(userData);
        setLogs(logData);
      })
      .catch((requestError) => {
        setError(requestError.response?.data?.detail || "Unable to load access management data.");
      });
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    try {
      await createUser(form);
      setForm({ username: "", email: "", password: "", role: "analyst" });
      await refresh();
    } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to create user."); }
  };

  return <div>
    <div className="page-heading"><div><p className="eyebrow">PHASE 10 · IAM</p><h1>Access Management</h1><p>Manage workspace identities, roles, and security audit activity.</p></div></div>
    {error && <p className="login-error" role="alert">{error}</p>}
    <div className="access-grid">
      <section className="panel settings-panel"><h3>Create user</h3><form className="access-form" onSubmit={submit}>
        <input placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
        <input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input type="password" minLength="12" placeholder="Password (12+ characters)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="analyst">Analyst</option><option value="viewer">Viewer</option><option value="admin">Admin</option></select>
        <button type="submit">Create account</button>
      </form></section>
      <section className="panel settings-panel"><h3>Workspace users</h3><div className="service-list">{users.map((item) => <div className="service-row" key={item.id}><div><strong>{item.username}</strong><small>{item.email} · {item.role}</small></div><button className="status-action" onClick={async () => { await updateUserStatus(item.id, !item.is_active); await refresh(); }}>{item.is_active ? "Deactivate" : "Activate"}</button></div>)}</div></section>
    </div>
    <section className="panel settings-panel audit-panel"><h3>Recent audit activity</h3>{logs.map((log) => <div className="service-row" key={log.id}><div><strong>{log.action}</strong><small>{log.user} · HTTP {log.status_code} · {new Date(log.created_at).toLocaleString()}</small></div></div>)}</section>
  </div>;
}
