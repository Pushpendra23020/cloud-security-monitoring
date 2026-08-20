import {
  Bell,
  Search,
  ShieldCheck,
  ChevronDown,
} from "lucide-react";

function Topbar() {
  return (
    <header className="topbar">
      <div className="search-box">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search incidents, IPs, users, assets..."
        />

        <span className="search-shortcut">⌘ K</span>
      </div>

      <div className="topbar-actions">
        <div className="system-secure">
          <ShieldCheck size={17} />
          <span>System Secure</span>
        </div>

        <button className="icon-button">
          <Bell size={19} />
          <span className="notification-dot"></span>
        </button>

        <div className="cloud-account">
          <div className="aws-badge">AWS</div>

          <div>
            <span>Production</span>
            <small>334767236854</small>
          </div>

          <ChevronDown size={16} />
        </div>

        <div className="avatar">PS</div>
      </div>
    </header>
  );
}

export default Topbar;
