from typing import Any

from app.models.security_event import SecurityEvent


class AssetMetadataEnricher:

    @staticmethod
    def _extract_tags_from_list(
        values: Any,
    ) -> dict[str, str]:
        tags: dict[str, str] = {}

        if not isinstance(values, list):
            return tags

        for item in values:
            if not isinstance(item, dict):
                continue

            key = (
                item.get("key")
                or item.get("Key")
            )

            value = (
                item.get("value")
                or item.get("Value")
            )

            if key is not None:
                tags[str(key)] = (
                    ""
                    if value is None
                    else str(value)
                )

        return tags

    @classmethod
    def extract_tags(
        cls,
        event: SecurityEvent,
    ) -> dict[str, str]:
        raw = event.raw_event or {}

        request = (
            raw.get("requestParameters")
            or {}
        )

        response = (
            raw.get("responseElements")
            or {}
        )

        tags: dict[str, str] = {}

        for key in (
            "tags",
            "tagSet",
        ):
            value = request.get(key)

            if isinstance(value, dict):
                value = (
                    value.get("items")
                    or value.get("item")
                    or []
                )

            tags.update(
                cls._extract_tags_from_list(
                    value
                )
            )

        tag_specification_set = (
            request.get(
                "tagSpecificationSet"
            )
            or {}
        )

        specifications = (
            tag_specification_set.get(
                "items"
            )
            or []
        )

        for specification in specifications:
            if not isinstance(
                specification,
                dict,
            ):
                continue

            specification_tags = (
                specification.get("tags")
                or specification.get(
                    "tagSet"
                )
                or {}
            )

            if isinstance(
                specification_tags,
                dict,
            ):
                specification_tags = (
                    specification_tags.get(
                        "items"
                    )
                    or []
                )

            tags.update(
                cls._extract_tags_from_list(
                    specification_tags
                )
            )

        instances_set = (
            response.get(
                "instancesSet"
            )
            or {}
        )

        instances = (
            instances_set.get("items")
            or []
        )

        for instance in instances:
            if not isinstance(
                instance,
                dict,
            ):
                continue

            tag_set = (
                instance.get("tagSet")
                or {}
            )

            if isinstance(tag_set, dict):
                tag_set = (
                    tag_set.get("items")
                    or []
                )

            tags.update(
                cls._extract_tags_from_list(
                    tag_set
                )
            )

        return tags

    @staticmethod
    def infer_name(
        tags: dict[str, str],
    ) -> str | None:
        return (
            tags.get("Name")
            or tags.get("name")
        )

    @staticmethod
    def infer_resource_state(
        event: SecurityEvent,
    ) -> str | None:
        event_name = (
            event.event_name or ""
        ).lower()

        state_map = {
            "runinstances": "running",
            "startinstances": "running",
            "rebootinstances": "running",
            "stopinstances": "stopped",
            "terminateinstances": "terminated",
        }

        if event_name in state_map:
            return state_map[event_name]

        raw = event.raw_event or {}

        response = (
            raw.get("responseElements")
            or {}
        )

        instances_set = (
            response.get(
                "instancesSet"
            )
            or {}
        )

        instances = (
            instances_set.get("items")
            or []
        )

        for instance in instances:
            if not isinstance(
                instance,
                dict,
            ):
                continue

            state = instance.get(
                "instanceState"
            )

            if isinstance(state, dict):
                state_name = state.get(
                    "name"
                )

                if state_name:
                    return str(
                        state_name
                    ).lower()

        return None

    @staticmethod
    def infer_public_exposure(
        event: SecurityEvent,
    ) -> bool | None:
        raw = event.raw_event or {}

        request = (
            raw.get("requestParameters")
            or {}
        )

        response = (
            raw.get("responseElements")
            or {}
        )

        network_interfaces = (
            request.get(
                "networkInterfaceSet"
            )
            or {}
        )

        interface_items = (
            network_interfaces.get(
                "items"
            )
            or []
        )

        for interface in interface_items:
            if not isinstance(
                interface,
                dict,
            ):
                continue

            if (
                "associatePublicIpAddress"
                in interface
            ):
                return bool(
                    interface[
                        "associatePublicIpAddress"
                    ]
                )

        instances_set = (
            response.get(
                "instancesSet"
            )
            or {}
        )

        instances = (
            instances_set.get("items")
            or []
        )

        for instance in instances:
            if not isinstance(
                instance,
                dict,
            ):
                continue

            if instance.get(
                "publicIpAddress"
            ):
                return True

        return None

    @classmethod
    def enrich(
        cls,
        event: SecurityEvent,
    ) -> dict:
        tags = cls.extract_tags(event)

        return {
            "name": (
                cls.infer_name(tags)
                if tags
                else None
            ),

            "tags": (
                tags
                if tags
                else None
            ),

            "resource_state": (
                cls.infer_resource_state(
                    event
                )
            ),

            "public_exposure": (
                cls.infer_public_exposure(
                    event
                )
            ),
        }
