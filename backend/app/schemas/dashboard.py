from pydantic import BaseModel
from datetime import datetime


class AssetSummary(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int


class AlertSummary(BaseModel):
    total: int
    open: int
    critical: int
    high: int
    medium: int
    low: int


class IncidentSummary(BaseModel):
    total: int
    open: int
    critical: int
    high: int
    medium: int
    low: int


class FindingSummary(BaseModel):
    total: int
    open: int
    critical: int
    high: int
    medium: int
    low: int


class DashboardSummaryResponse(BaseModel):
    assets: AssetSummary
    alerts: AlertSummary
    incidents: IncidentSummary
    findings: FindingSummary


class SeverityDistributionResponse(BaseModel):
    critical: int
    high: int
    medium: int
    low: int


class RiskSummaryResponse(BaseModel):
    total_assets: int
    average_risk_score: float
    critical: int
    high: int
    medium: int
    low: int
    public_exposure: int


class RecentAlertItem(BaseModel):
    alert_id: str
    rule_name: str
    severity: str
    status: str
    cloud_provider: str
    account_id: str | None = None
    region: str | None = None
    source_ip: str | None = None
    created_at: datetime


class RecentAlertsResponse(BaseModel):
    total: int
    items: list[RecentAlertItem]


class RecentIncidentItem(BaseModel):
    incident_id: str
    title: str
    severity: str
    status: str
    cloud_provider: str
    account_id: str | None = None
    region: str | None = None
    created_at: datetime


class RecentIncidentsResponse(BaseModel):
    total: int
    items: list[RecentIncidentItem]
