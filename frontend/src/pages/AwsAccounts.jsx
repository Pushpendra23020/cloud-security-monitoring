import { useEffect, useState } from "react";
import { createCloudAccount, deleteCloudAccount, listCloudAccounts, testCloudAccount, updateCloudAccount } from "../api/cloudAccountsApi";

const emptyForm = { name: "", account_id: "", region: "ap-south-1", role_arn: "", external_id: "", description: "" };

export default function AwsAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState("");
  const load = async () => setAccounts(await listCloudAccounts());
  useEffect(() => {
    let active = true;
    listCloudAccounts()
      .then((data) => { if (active) setAccounts(data); })
      .catch(() => { if (active) setMessage("Unable to load AWS accounts."); });
    return () => { active = false; };
  }, []);

  const submit = async (event) => {
    event.preventDefault(); setMessage("");
    try {
      await createCloudAccount({ ...form, provider: "aws", auth_method: "assume_role", external_id: form.external_id || null });
      setForm(emptyForm); setShowForm(false); await load();
    } catch (error) { setMessage(error.response?.data?.detail || "Account could not be added."); }
  };

  const test = async (account) => {
    setMessage(`Testing ${account.name}...`);
    try { const result = await testCloudAccount(account.id); setMessage(result.message); await load(); }
    catch (error) { setMessage(error.response?.data?.detail || "Connection test failed."); await load(); }
  };

  const toggle = async (account) => { await updateCloudAccount(account.id, { monitoring_enabled: !account.monitoring_enabled }); await load(); };
  const remove = async (account) => { if (window.confirm(`Remove ${account.name}? Historical findings will be retained where possible.`)) { await deleteCloudAccount(account.id); await load(); } };

  return <div>
    <div className="page-heading"><div><p className="eyebrow">ADMINISTRATION</p><h1>AWS Accounts</h1><p>Manage cross-account monitoring through temporary STS credentials.</p></div><button className="primary-button" onClick={() => setShowForm(!showForm)}>Add AWS Account</button></div>
    {message && <div className="panel status-message">{message}</div>}
    {showForm && <form className="panel account-form" onSubmit={submit}>
      <h3>Connect AWS Account</h3><p>Deploy the read-only monitoring role in the customer account, then enter its metadata. Credentials are never displayed or sent to the browser.</p>
      <div className="form-grid">
        <label>Account name<input required value={form.name} onChange={(e) => setForm({...form, name:e.target.value})} /></label>
        <label>AWS Account ID<input required pattern="[0-9]{12}" value={form.account_id} onChange={(e) => setForm({...form, account_id:e.target.value})} /></label>
        <label>Region<input required value={form.region} onChange={(e) => setForm({...form, region:e.target.value})} /></label>
        <label>Role ARN<input required placeholder="arn:aws:iam::123456789012:role/CloudSecurityMonitoringReadOnly" value={form.role_arn} onChange={(e) => setForm({...form, role_arn:e.target.value})} /></label>
        <label>External ID<input type="password" minLength="8" value={form.external_id} onChange={(e) => setForm({...form, external_id:e.target.value})} /></label>
        <label>Description<input value={form.description} onChange={(e) => setForm({...form, description:e.target.value})} /></label>
      </div><button className="primary-button" type="submit">Save account</button>
    </form>}
    <div className="panel table-wrap"><table><thead><tr><th>Account</th><th>AWS Account ID</th><th>Region</th><th>Authentication</th><th>Monitoring</th><th>Health</th><th>Last Sync</th><th>Actions</th></tr></thead><tbody>
      {accounts.map((account) => <tr key={account.id}><td><strong>{account.name}</strong></td><td>{account.account_id}</td><td>{account.region || "—"}</td><td>IAM Role</td><td>{account.monitoring_enabled ? "Enabled" : "Disabled"}</td><td><span className={`severity-badge ${account.health_status}`}>{account.health_status}</span></td><td>{account.last_sync ? new Date(account.last_sync).toLocaleString() : "Never"}</td><td className="action-cell"><button onClick={() => test(account)}>Test</button><button onClick={() => toggle(account)}>{account.monitoring_enabled ? "Disable" : "Enable"}</button><button onClick={() => remove(account)}>Remove</button></td></tr>)}
      {!accounts.length && <tr><td colSpan="8" className="empty-cell">No AWS accounts connected yet. Connect your first account to begin monitoring.</td></tr>}
    </tbody></table></div>
  </div>;
}
