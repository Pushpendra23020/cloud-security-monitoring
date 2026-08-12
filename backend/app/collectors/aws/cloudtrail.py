from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


class CloudTrailCollector:
    def __init__(self, client):
        self.client = client

    def collect_events(
        self,
        lookback_minutes: int = 60,
        max_results: int = 50,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        if start_time is None:
            start_time = end_time - timedelta(
                minutes=lookback_minutes
            )

        events: List[Dict[str, Any]] = []

        kwargs = {
            "StartTime": start_time,
            "EndTime": end_time,
            "MaxResults": max_results,
        }

        while True:
            response = self.client.lookup_events(**kwargs)

            events.extend(
                response.get("Events", [])
            )

            next_token = response.get("NextToken")

            if not next_token:
                break

            kwargs["NextToken"] = next_token

        return events