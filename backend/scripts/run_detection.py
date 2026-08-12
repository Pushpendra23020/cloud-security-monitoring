import json
from pathlib import Path

from app.models.security_event import SecurityEvent
from app.pipeline.detection_pipeline import DetectionPipeline


EVENT_FILE = Path(
    "data/normalized/security_events.jsonl"
)


def load_events():
    if not EVENT_FILE.exists():
        raise FileNotFoundError(
            f"Security event file not found: {EVENT_FILE}"
        )

    with EVENT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)

                yield SecurityEvent.model_validate(
                    data
                )

            except Exception as exc:
                print(
                    f"[ERROR] line={line_number} "
                    f"error={exc}"
                )


def main():
    pipeline = DetectionPipeline()

    processed = 0
    alerts_generated = 0

    print(
        "\n=== Cloud Security Detection Run ===\n"
    )

    for event in load_events():
        processed += 1

        alerts = pipeline.process(event)

        if not alerts:
            continue

        alerts_generated += len(alerts)

        for alert in alerts:
            print(
                "[ALERT]"
                f" severity={alert.severity.upper()}"
                f" rule={alert.rule_id}"
                f" event={alert.event_name}"
                f" account={alert.account_id}"
                f" region={alert.region}"
                f" source_ip={alert.source_ip}"
            )

            print(
                f"        {alert.rule_name}"
            )

    print(
        "\n=== Detection Summary ==="
    )

    print(
        f"Events processed: {processed}"
    )

    print(
        f"Alerts generated: {alerts_generated}"
    )


if __name__ == "__main__":
    main()
