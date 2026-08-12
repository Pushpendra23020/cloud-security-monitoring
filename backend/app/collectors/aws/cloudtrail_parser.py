import json
from typing import Any, Dict, List


def parse_lookup_events(
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    parsed_events = []

    for event in events:
        cloudtrail_event = event.get("CloudTrailEvent")

        if not cloudtrail_event:
            continue

        if isinstance(cloudtrail_event, str):
            raw_event = json.loads(cloudtrail_event)
        else:
            raw_event = cloudtrail_event

        parsed_events.append(raw_event)

    return parsed_events
