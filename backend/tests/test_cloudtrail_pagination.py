from app.collectors.aws.cloudtrail import (
    CloudTrailCollector,
)


class FakeCloudTrailClient:
    def __init__(self):
        self.calls = 0
        self.received_kwargs = []

    def lookup_events(self, **kwargs):
        self.calls += 1
        self.received_kwargs.append(kwargs.copy())

        if self.calls == 1:
            return {
                "Events": [
                    {
                        "EventId": "event-001",
                        "EventName": "ConsoleLogin",
                    }
                ],
                "NextToken": "token-page-2",
            }

        return {
            "Events": [
                {
                    "EventId": "event-002",
                    "EventName": "CreateAccessKey",
                }
            ]
        }


def test_cloudtrail_pagination():
    fake_client = FakeCloudTrailClient()

    collector = CloudTrailCollector(
        client=fake_client
    )

    events = collector.collect_events(
        lookback_minutes=60,
        max_results=50,
    )

    assert len(events) == 2

    assert events[0]["EventId"] == "event-001"
    assert events[1]["EventId"] == "event-002"

    assert fake_client.calls == 2

    assert (
        fake_client.received_kwargs[1]["NextToken"]
        == "token-page-2"
    )
