import { useState } from "react";

export default function Settings() {
  const [notifications, setNotifications] = useState(true);
  return <div>
    <div className="page-heading"><div><p className="eyebrow">CONFIGURATION</p><h1>Settings</h1><p>Manage your production workspace preferences.</p></div></div>
    <div className="panel settings-panel">
      <h3>Notifications</h3>
      <label className="setting-row"><div><strong>Security alert notifications</strong><small>Show notifications for critical and high-severity detections.</small></div><input type="checkbox" checked={notifications} onChange={(event) => setNotifications(event.target.checked)} /></label>
      <h3>AWS environment</h3>
      <div className="setting-row"><div><strong>Production</strong><small>Account 334767236854 · CloudTrail monitoring enabled</small></div><span className="connected-label">● Connected</span></div>
    </div>
  </div>;
}
