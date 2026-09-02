import {
  Bell,
  Building2,
  Check,
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
  const [switchingOrganizationId, setSwitchingOrganizationId] = useState(null);
  const [workspaceError, setWorkspaceError] = useState("");
  const actionsRef = useRef(null);
  const searchInputRef = useRef(null);
  const navigate = useNavigate();
  const {
    enabled: authEnabled,
    user,
    organizations,
    currentOrganization,
    logout,
    switchOrganization,
  } = useAuth();
  const displayName = user?.username || "Pushpendra Singh";
  const initials = displayName.split(/[ ._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "PS";
  const canSwitchWorkspace = organizations.length > 1;

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

  const selectOrganization = async (organizationId) => {
    setWorkspaceError("");
    setSwitchingOrganizationId(organizationId);
    try {
      await switchOrganization(organizationId);
    } catch (error) {
      setWorkspaceError(
        error.response?.data?.detail || error.message || "Unable to switch workspace."
      );
      setSwitchingOrganizationId(null);
    }
  };

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

        {currentOrganization && <div className="topbar-menu-wrap">
          {canSwitchWorkspace ? <button
            className="cloud-account topbar-control"
            type="button"
            aria-label={`Current workspace: ${currentOrganization.name}. Open workspace switcher`}
            aria-haspopup="menu"
            aria-expanded={openMenu === "workspace"}
            onClick={() => toggleMenu("workspace")}
          >
            <div className="workspace-badge"><Building2 size={14} /></div>
            <div className="workspace-summary">
              <span>{currentOrganization.name}</span>
              <small>{currentOrganization.role} workspace</small>
            </div>
            <ChevronDown size={16} />
          </button> : <div
            className="cloud-account single-workspace"
            aria-label={`Current workspace: ${currentOrganization.name}`}
          >
            <div className="workspace-badge"><Building2 size={14} /></div>
            <div className="workspace-summary">
              <span>{currentOrganization.name}</span>
              <small>{currentOrganization.role} workspace</small>
            </div>
          </div>}
          {canSwitchWorkspace && openMenu === "workspace" && (
            <div className="topbar-popover workspace-popover" role="menu" aria-label="Switch workspace">
              <strong>Switch workspace</strong>
              <small>Select the organization whose security data you want to view.</small>
              <div className="workspace-options">
                {organizations.map((organization) => <button
                  className={`workspace-option ${organization.is_current ? "current" : ""}`}
                  type="button"
                  role="menuitemradio"
                  aria-checked={organization.is_current}
                  disabled={organization.is_current || switchingOrganizationId !== null}
                  key={organization.organization_id}
                  onClick={() => selectOrganization(organization.organization_id)}
                >
                  <span>
                    <strong>{organization.name}</strong>
                    <small>{organization.role}</small>
                  </span>
                  {organization.is_current
                    ? <Check size={16} aria-label="Current workspace" />
                    : switchingOrganizationId === organization.organization_id
                      ? <small>Switching…</small>
                      : null}
                </button>)}
              </div>
              {workspaceError && <p className="workspace-switch-error" role="alert">{workspaceError}</p>}
            </div>
          )}
        </div>}

        <div className="topbar-menu-wrap">
          <button className="avatar topbar-control" type="button" aria-label="Open profile menu" aria-expanded={openMenu === "profile"} onClick={() => toggleMenu("profile")}>{initials}</button>
          {openMenu === "profile" && (
            <div className="topbar-popover profile-popover">
              <strong>{displayName}</strong>
              <small>{user?.role ? `${user.role[0].toUpperCase()}${user.role.slice(1)}` : "Security Administrator"}</small>
              <button type="button" onClick={() => { navigate("/settings"); setOpenMenu(null); }}>Profile & settings</button>
              {authEnabled && <button className="logout-button" type="button" onClick={async () => { await logout(); navigate("/login"); }}>Sign out</button>}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Topbar;
