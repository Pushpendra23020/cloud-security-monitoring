from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models.alert import Alert
from app.database.models.asset import Asset
from app.database.models.finding import Finding
from app.database.models.incident import Incident

from app.schemas.dashboard import (
    AlertSummary,
    AssetSummary,
    DashboardSummaryResponse,
    FindingSummary,
    IncidentSummary,
    RecentAlertItem,
    RecentAlertsResponse,
    RecentIncidentItem,
    RecentIncidentsResponse,
    RiskSummaryResponse,
    SeverityDistributionResponse,
)

class DashboardService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get_summary(
        self,
    ) -> DashboardSummaryResponse:
        return DashboardSummaryResponse(
            assets=self._get_asset_summary(),
            alerts=self._get_alert_summary(),
            incidents=self._get_incident_summary(),
            findings=self._get_finding_summary(),
        )

    def _get_asset_summary(
        self,
    ) -> AssetSummary:
        counts = self._group_counts(
            Asset.risk_level
        )

        total = self._count(Asset)

        return AssetSummary(
            total=total,
            critical=counts.get(
                "critical",
                0,
            ),
            high=counts.get(
                "high",
                0,
            ),
            medium=counts.get(
                "medium",
                0,
            ),
            low=counts.get(
                "low",
                0,
            ),
        )

    def _get_alert_summary(
        self,
    ) -> AlertSummary:
        severity_counts = self._group_counts(
            Alert.severity
        )

        total = self._count(Alert)

        open_count = (
            self.db.query(
                func.count(Alert.id)
            )
            .filter(
                func.lower(Alert.status)
                == "open"
            )
            .scalar()
            or 0
        )

        return AlertSummary(
            total=total,
            open=open_count,
            critical=severity_counts.get(
                "critical",
                0,
            ),
            high=severity_counts.get(
                "high",
                0,
            ),
            medium=severity_counts.get(
                "medium",
                0,
            ),
            low=severity_counts.get(
                "low",
                0,
            ),
        )

    def _get_incident_summary(
        self,
    ) -> IncidentSummary:
        severity_counts = self._group_counts(
            Incident.severity
        )

        total = self._count(Incident)

        open_count = (
            self.db.query(
                func.count(Incident.id)
            )
            .filter(
                func.lower(Incident.status)
                == "open"
            )
            .scalar()
            or 0
        )

        return IncidentSummary(
            total=total,
            open=open_count,
            critical=severity_counts.get(
                "critical",
                0,
            ),
            high=severity_counts.get(
                "high",
                0,
            ),
            medium=severity_counts.get(
                "medium",
                0,
            ),
            low=severity_counts.get(
                "low",
                0,
            ),
        )

    def _get_finding_summary(
        self,
    ) -> FindingSummary:
        severity_counts = self._group_counts(
            Finding.severity
        )

        total = self._count(Finding)

        open_count = (
            self.db.query(
                func.count(Finding.id)
            )
            .filter(
                func.lower(Finding.status)
                == "open"
            )
            .scalar()
            or 0
        )

        return FindingSummary(
            total=total,
            open=open_count,
            critical=severity_counts.get(
                "critical",
                0,
            ),
            high=severity_counts.get(
                "high",
                0,
            ),
            medium=severity_counts.get(
                "medium",
                0,
            ),
            low=severity_counts.get(
                "low",
                0,
            ),
        )

    def _count(
        self,
        model,
    ) -> int:
        return (
            self.db.query(
                func.count(model.id)
            ).scalar()
            or 0
        )

    def _group_counts(
        self,
        column,
    ) -> dict[str, int]:
        rows = (
            self.db.query(
                func.lower(column),
                func.count(),
            )
            .group_by(
                func.lower(column)
            )
            .all()
        )

        return {
            str(key): count
            for key, count in rows
            if key is not None
        }
    def get_severity_distribution(
        self,
    ) -> SeverityDistributionResponse:
        counts = self._group_counts(
            Alert.severity
        )

        return SeverityDistributionResponse(
            critical=counts.get("critical", 0),
            high=counts.get("high", 0),
            medium=counts.get("medium", 0),
            low=counts.get("low", 0),
        )

    def get_risk_summary(
        self,
    ) -> RiskSummaryResponse:
        risk_counts = self._group_counts(
            Asset.risk_level
        )

        total_assets = self._count(Asset)

        average_risk_score = (
            self.db.query(
                func.avg(Asset.risk_score)
            ).scalar()
            or 0.0
        )

        public_exposure = (
            self.db.query(
                func.count(Asset.id)
            )
            .filter(
                Asset.public_exposure.is_(True)
            )
            .scalar()
            or 0
        )

        return RiskSummaryResponse(
            total_assets=total_assets,
            average_risk_score=round(
                float(average_risk_score),
                2,
            ),
            critical=risk_counts.get(
                "critical",
                0,
            ),
            high=risk_counts.get(
                "high",
                0,
            ),
            medium=risk_counts.get(
                "medium",
                0,
            ),
            low=risk_counts.get(
                "low",
                0,
            ),
            public_exposure=public_exposure,
        )

    def get_recent_alerts(
        self,
        limit: int = 6,
    ) -> RecentAlertsResponse:
        total = self._count(Alert)

        alerts = (
            self.db.query(Alert)
            .order_by(
                Alert.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        return RecentAlertsResponse(
            total=total,
            items=[
                RecentAlertItem(
                    alert_id=alert.alert_id,
                    rule_name=alert.rule_name,
                    severity=alert.severity,
                    status=alert.status,
                    cloud_provider=alert.cloud_provider,
                    account_id=alert.account_id,
                    region=alert.region,
                    source_ip=alert.source_ip,
                    created_at=alert.created_at,
                )
                for alert in alerts
            ],
        )

    def get_recent_incidents(
        self,
        limit: int = 6,
    ) -> RecentIncidentsResponse:
        total = self._count(Incident)

        incidents = (
            self.db.query(Incident)
            .order_by(
                Incident.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        return RecentIncidentsResponse(
            total=total,
            items=[
                RecentIncidentItem(
                    incident_id=incident.incident_id,
                    title=incident.title,
                    severity=incident.severity,
                    status=incident.status,
                    cloud_provider=incident.cloud_provider,
                    account_id=incident.account_id,
                    region=incident.region,
                    created_at=incident.created_at,
                )
                for incident in incidents
            ],
        )
