import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ShieldAlert,
  Bell,
  Crosshair,
  Server,
  ListChecks,
  Activity,
  Settings,
  Cloud,
} from "lucide-react";

const menuItems = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Incidents", path: "/incidents", icon: ShieldAlert },
  { name: "Alerts", path: "/alerts", icon: Bell },
  { name: "Threat Hunting", path: "/threat-hunting", icon: Crosshair },
  { name: "Cloud Assets", path: "/assets", icon: Server },
  { name: "Detection Rules", path: "/rules", icon: ListChecks },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <Cloud size={24} />
        </div>

        <div>
          <h2>Cloud Sentinel</h2>
          <span>Security Platform</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-label">SECURITY OPERATIONS</div>

        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={19} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="nav-item">
          <Activity size={19} />
          <span>System Health</span>
        </div>

        <div className="nav-item">
          <Settings size={19} />
          <span>Settings</span>
        </div>

        <div className="sensor-status">
          <span className="status-dot"></span>

          <div>
            <strong>Monitoring Active</strong>
            <small>AWS CloudTrail</small>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
