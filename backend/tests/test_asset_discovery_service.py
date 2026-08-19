from datetime import datetime, timezone

from app.models.security_event import (
    SecurityEvent,
)
from app.services.asset_discovery_service import (
    AssetDiscoveryService,
)


def make_event(
    *,
    event_name="StopInstances",
    resource_id="i-phase5-test-001",
    resource_type="ec2_instance",
):
    return SecurityEvent(
        event_id="asset-discovery-test",
        timestamp=datetime.now(
            timezone.utc
        ),
        cloud_provider="aws",
        account_id="123456789012",
        region="ap-south-1",
        service="ec2",
        event_name=event_name,
        resource_type=resource_type,
        resource_id=resource_id,
    )


def test_resource_state_running():
    event = make_event(
        event_name="StartInstances"
    )

    assert (
        AssetDiscoveryService
        .infer_resource_state(event)
        == "running"
    )


def test_resource_state_stopped():
    event = make_event(
        event_name="StopInstances"
    )

    assert (
        AssetDiscoveryService
        .infer_resource_state(event)
        == "stopped"
    )


def test_resource_state_terminated():
    event = make_event(
        event_name="TerminateInstances"
    )

    assert (
        AssetDiscoveryService
        .infer_resource_state(event)
        == "terminated"
    )


def test_unknown_resource_state():
    event = make_event(
        event_name="DescribeInstances"
    )

    assert (
        AssetDiscoveryService
        .infer_resource_state(event)
        == "unknown"
    )
