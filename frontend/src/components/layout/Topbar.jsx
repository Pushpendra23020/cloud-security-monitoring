import {
  Bell,
  Search,
  ShieldCheck,
  ChevronDown,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/authState";

function Topbar() {
  const [openMenu, setOpenMenu] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const actionsRef = useRef(null);
  const searchInputRef = useRef(null);
  const navigate = useNavigate();
  const { enabled: authEnabled, user, logout } = useAuth();
  const displayName = user?.username || "Pushpendra Singh";
  const initials = displayName.split(/[ ._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "PS";

  useEffect(() => {
    const closeMenus = (event) => {
      if (!actionsRef.current?.contains(event.target)) setOpenMenu(null);
    };
    document.addEventListener("mousedown", closeMenus);
    return () => document.removeEventListener("mousedown", closeMenus);
  }, []);

  useEffect(() => {
    const focusSearch = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    document.addEventListener("keydown", focusSearch);
    return () => document.removeEventListener("keydown", focusSearch);
  }, []);

  const submitSearch = (event) => {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query) {
      searchInputRef.current?.focus();
      return;
    }
    navigate(`/threat-hunting?q=${encodeURIComponent(query)}`);
  };

  const toggleMenu = (menu) => setOpenMenu((current) => current === menu ? null : menu);

  return (
    <header className="topbar">
      <form className="search-box" role="search" onSubmit={submitSearch}>
        <button className="global-search-button" type="submit" aria-label="Run global security search">
          <Search size={18} />
        </button>

        <input
          ref={searchInputRef}
          type="text"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Search incidents, IPs, users, assets..."
          aria-label="Global security search"
        />

        <span className="search-shortcut">⌘ K</span>
      </form>

      <div className="topbar-actions" ref={actionsRef}>
        <div className="system-secure">
          <ShieldCheck size={17} />
          <span>System Secure</span>
        </div>

        <div className="topbar-menu-wrap">
        <button className="icon-button" type="button" aria-label="Notifications" aria-expanded={openMenu === "notifications"} onClick={() => toggleMenu("notifications")}>
          <Bell size={19} />
          <span className="notification-dot"></span>
        </button>
        {openMenu === "notifications" && (
          <div className="topbar-popover notification-popover">
            <strong>Notifications</strong>
            <p><span className="severity-dot critical" />Critical IAM policy change detected</p>
            <p><span className="severity-dot warning" />Unusual API activity in production</p>
            <button type="button" onClick={() => { navigate("/alerts"); setOpenMenu(null); }}>View all alerts</button>
          </div>
        )}
        </div>

        <div className="topbar-menu-wrap">
        <button className="cloud-account topbar-control" type="button" aria-expanded={openMenu === "account"} onClick={() => toggleMenu("account")}>
          <div className="aws-badge">AWS</div>

          <div>
            <span>Production</span>
            <small>334767236854</small>
          </div>

          <ChevronDown size={16} />
        </button>
        {openMenu === "account" && (
          <div className="topbar-popover account-popover">
            <strong>AWS account</strong>
            <p>Production <small>334767236854</small></p>
            <span className="connected-label">● Connected</span>
          </div>
        )}
        </div>

        <div className="topbar-menu-wrap">
          <button className="avatar topbar-control" type="button" aria-label="Open profile menu" aria-expanded={openMenu === "profile"} onClick={() => toggleMenu("profile")}>{initials}</button>
          {openMenu === "profile" && (
            <div className="topbar-popover profile-popover">
              <strong>{displayName}</strong>
              <small>{user?.role ? `${user.role[0].toUpperCase()}${user.role.slice(1)}` : "Security Administrator"}</small>
              <button type="button" onClick={() => { navigate("/settings"); setOpenMenu(null); }}>Profile & settings</button>
              {authEnabled && <button className="logout-button" type="button" onClick={() => { logout(); navigate("/login"); }}>Sign out</button>}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Topbar;
