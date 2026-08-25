import { Activity, CheckCircle2, Cloud, Database, Server } from "lucide-react";

const services = [
  { name: "Backend API", detail: "Operational", icon: Server },
  { name: "PostgreSQL", detail: "Connected", icon: Database },
  { name: "AWS CloudTrail", detail: "Monitoring active", icon: Cloud },
];

export default function SystemHealth() {
  return <div>
    <div className="page-heading"><div><p className="eyebrow">PLATFORM</p><h1>System Health</h1><p>Live status of security monitoring services.</p></div></div>
    <div className="panel settings-panel">
      <div className="health-summary"><Activity size={22} /><div><strong>All systems operational</strong><small>Production environment</small></div></div>
      <div className="service-list">{services.map(({ name, detail, icon: Icon }) => <div className="service-row" key={name}><Icon size={20} /><div><strong>{name}</strong><small>{detail}</small></div><CheckCircle2 className="service-ok" size={20} /></div>)}</div>
    </div>
  </div>;
}
