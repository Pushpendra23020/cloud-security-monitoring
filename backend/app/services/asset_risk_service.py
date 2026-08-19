from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.alert import Alert as AlertDB
from app.database.models.asset import Asset
from app.database.models.finding import Finding as FindingDB


class AssetRiskService:

    SEVERITY_WEIGHTS = {
        "critical": 35,
        "high": 20,
        "medium": 10,
        "low": 4,
        "info": 1,
    }

    ALERT_STATUS_MULTIPLIERS = {
        "open": 1.0,
        "acknowledged": 0.9,
        "investigating": 1.0,
        "resolved": 0.0,
        "false_positive": 0.0,
    }

    FINDING_STATUS_MULTIPLIERS = {
        "open": 1.0,
        "investigating": 1.0,
        "resolved": 0.0,
        "closed": 0.0,
        "false_positive": 0.0,
    }

    @staticmethod
    def calculate_risk_level(
        risk_score: int,
    ) -> str:
        if risk_score >= 80:
            return "critical"

        if risk_score >= 60:
            return "high"

        if risk_score >= 30:
            return "medium"

        return "low"

    @staticmethod
    def calculate_age_multiplier(
        created_at: datetime | None,
        *,
        now: datetime | None = None,
    ) -> float:
        if created_at is None:
            return 1.0

        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        if current_time.tzinfo is None:
            current_time = (
                current_time.replace(
                    tzinfo=timezone.utc
                )
            )

        if created_at.tzinfo is None:
            created_at = (
                created_at.replace(
                    tzinfo=timezone.utc
                )
            )

        age_seconds = max(
            0,
            (
                current_time
                - created_at
            ).total_seconds(),
        )

        age_hours = (
            age_seconds / 3600
        )

        if age_hours <= 24:
            return 1.0

        if age_hours <= (24 * 7):
            return 0.85

        if age_hours <= (24 * 30):
            return 0.60

        return 0.35

    @classmethod
    def calculate_alert_contribution(
        cls,
        *,
        severity: str | None,
        status: str | None,
        created_at: datetime | None = None,
        now: datetime | None = None,
    ) -> float:
        severity_value = str(
            severity or ""
        ).lower()

        status_value = str(
            status or "open"
        ).lower()

        base_score = (
            cls.SEVERITY_WEIGHTS.get(
                severity_value,
                0,
            )
        )

        status_multiplier = (
            cls.ALERT_STATUS_MULTIPLIERS.get(
                status_value,
                1.0,
            )
        )

        age_multiplier = (
            cls.calculate_age_multiplier(
                created_at,
                now=now,
            )
        )

        return (
            base_score
            * status_multiplier
            * age_multiplier
        )

    @classmethod
    def calculate_finding_contribution(
        cls,
        *,
        severity: str | None,
        status: str | None,
        created_at: datetime | None = None,
        now: datetime | None = None,
    ) -> float:
        severity_value = str(
            severity or ""
        ).lower()

        status_value = str(
            status or "open"
        ).lower()

        base_score = (
            cls.SEVERITY_WEIGHTS.get(
                severity_value,
                0,
            )
        )

        status_multiplier = (
            cls.FINDING_STATUS_MULTIPLIERS.get(
                status_value,
                1.0,
            )
        )

        age_multiplier = (
            cls.calculate_age_multiplier(
                created_at,
                now=now,
            )
        )

        return (
            base_score
            * status_multiplier
            * age_multiplier
        )

    @classmethod
    def enrich_asset(
        cls,
        db: Session,
        asset: Asset,
        *,
        commit: bool = True,
    ) -> Asset:
        alert_statement = (
            select(AlertDB)
            .where(
                AlertDB.resource_id
                == asset.asset_id
            )
        )

        alerts = list(
            db.scalars(
                alert_statement
            ).all()
        )

        finding_statement = (
            select(FindingDB)
            .where(
                FindingDB.asset_id
                == asset.id
            )
        )

        findings = list(
            db.scalars(
                finding_statement
            ).all()
        )

        now = datetime.now(
            timezone.utc
        )

        risk_score = 0.0

        active_alerts_count = 0
        active_findings_count = 0

        for alert in alerts:
            contribution = (
                cls.calculate_alert_contribution(
                    severity=alert.severity,
                    status=alert.status,
                    created_at=alert.created_at,
                    now=now,
                )
            )

            risk_score += contribution

            if contribution > 0:
                active_alerts_count += 1

        for finding in findings:
            contribution = (
                cls.calculate_finding_contribution(
                    severity=finding.severity,
                    status=finding.status,
                    created_at=finding.created_at,
                    now=now,
                )
            )

            risk_score += contribution

            if contribution > 0:
                active_findings_count += 1

        if asset.public_exposure:
            risk_score += 15

        risk_score = int(
            round(
                max(
                    0,
                    min(
                        risk_score,
                        100,
                    ),
                )
            )
        )

        asset.alerts_count = (
            active_alerts_count
        )

        asset.findings_count = (
            active_findings_count
        )

        asset.risk_score = risk_score

        asset.risk_level = (
            cls.calculate_risk_level(
                risk_score
            )
        )
        asset.risk_updated_at = (
       datetime.now(timezone.utc)
       )
        if commit:
            db.commit()
            db.refresh(asset)
        else:
            db.flush()

        return asset
    @classmethod
    def explain_asset_risk(
        cls,
        db: Session,
        asset: Asset,
    ) -> dict:
        alert_statement = (
            select(AlertDB)
            .where(
                AlertDB.resource_id
                == asset.asset_id
            )
        )

        alerts = list(
            db.scalars(
                alert_statement
            ).all()
        )

        finding_statement = (
            select(FindingDB)
            .where(
                FindingDB.asset_id
                == asset.id
            )
        )

        findings = list(
            db.scalars(
                finding_statement
            ).all()
        )

        now = datetime.now(
            timezone.utc
        )

        components = []
        total = 0.0

        for alert in alerts:
            contribution = (
                cls.calculate_alert_contribution(
                    severity=alert.severity,
                    status=alert.status,
                    created_at=alert.created_at,
                    now=now,
                )
            )

            total += contribution

            components.append(
                {
                    "type": "alert",
                    "id": alert.alert_id,
                    "severity": alert.severity,
                    "status": alert.status,
                    "contribution": round(
                        contribution,
                        2,
                    ),
                }
            )

        for finding in findings:
            contribution = (
                cls.calculate_finding_contribution(
                    severity=finding.severity,
                    status=finding.status,
                    created_at=finding.created_at,
                    now=now,
                )
            )

            total += contribution

            components.append(
                {
                    "type": "finding",
                    "id": finding.id,
                    "severity": finding.severity,
                    "status": finding.status,
                    "contribution": round(
                        contribution,
                        2,
                    ),
                }
            )

        if asset.public_exposure:
            total += 15

            components.append(
                {
                    "type": "exposure",
                    "label": "Public exposure",
                    "contribution": 15,
                }
            )

        final_score = int(
            round(
                max(
                    0,
                    min(total, 100),
                )
            )
        )

        return {
            "asset_id": asset.asset_id,
            "risk_score": final_score,
            "risk_level": (
                cls.calculate_risk_level(
                    final_score
                )
            ),
            "components": components,
        }
