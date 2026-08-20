function MetricCard({
  title,
  value,
  change,
  icon: Icon,
  severity,
}) {
  return (
    <div className={`metric-card ${severity || ""}`}>
      <div className="metric-card-header">
        <span>{title}</span>

        {Icon && (
          <div className="metric-icon">
            <Icon size={20} />
          </div>
        )}
      </div>

      <div className="metric-value">{value}</div>

      <div className="metric-change">{change}</div>
    </div>
  );
}

export default MetricCard;
