from datetime import datetime, timezone

from app.models.security_event import SecurityEvent
from app.services.asset_metadata_enricher import (
    AssetMetadataEnricher,
)


def make_event(
    event_name="RunInstances",
    raw_event=None,
):
    return SecurityEvent(
        event_id="metadata-test",
        timestamp=datetime.now(
            timezone.utc
        ),
        cloud_provider="aws",
        account_id="123456789012",
        region="ap-south-1",
        service="ec2",
        event_name=event_name,
        resource_type="ec2_instance",
        resource_id="i-metadata-test",
        raw_event=raw_event or {},
    )


def test_extracts_name_tag():
    event = make_event(
        raw_event={
            "requestParameters": {
                "tagSpecificationSet": {
                    "items": [
                        {
                            "resourceType":
                                "instance",
                            "tags": {
                                "items": [
                                    {
                                        "key":
                                            "Name",
                                        "value":
                                            "Production-Web",
                                    },
                                    {
                                        "key":
                                            "Environment",
                                        "value":
                                            "production",
                                    },
                                ]
                            },
                        }
                    ]
                }
            }
        }
    )

    metadata = (
        AssetMetadataEnricher
        .enrich(event)
    )

    assert (
        metadata["name"]
        == "Production-Web"
    )

    assert (
        metadata["tags"][
            "Environment"
        ]
        == "production"
    )


def test_stop_instance_state():
    event = make_event(
        event_name="StopInstances"
    )

    metadata = (
        AssetMetadataEnricher
        .enrich(event)
    )

    assert (
        metadata["resource_state"]
        == "stopped"
    )


def test_detects_public_ip_request():
    event = make_event(
        raw_event={
            "requestParameters": {
                "networkInterfaceSet": {
                    "items": [
                        {
                            "associatePublicIpAddress":
                                True
                        }
                    ]
                }
            }
        }
    )

    metadata = (
        AssetMetadataEnricher
        .enrich(event)
    )

    assert (
        metadata[
            "public_exposure"
        ]
        is True
    )


def test_unknown_exposure_returns_none():
    event = make_event()

    metadata = (
        AssetMetadataEnricher
        .enrich(event)
    )

    assert (
        metadata["public_exposure"]
        is None
    )

def test_unknown_state_returns_none():
    event = make_event(
        event_name="DescribeInstances"
    )

    metadata = (
        AssetMetadataEnricher
        .enrich(event)
    )

    assert (
        metadata["resource_state"]
        is None
    )
