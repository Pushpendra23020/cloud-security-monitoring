from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database.session import RLS_TABLES, TENANT_SETTING, engine


def test_all_tenant_tables_have_forced_row_level_security():
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT relname, relrowsecurity, relforcerowsecurity
                FROM pg_class
                WHERE relname = ANY(:tables)
                """
            ),
            {"tables": list(RLS_TABLES)},
        ).all()

    status = {
        row.relname: (row.relrowsecurity, row.relforcerowsecurity)
        for row in rows
    }
    assert set(status) == set(RLS_TABLES)
    assert all(enabled and forced for enabled, forced in status.values())


def test_runtime_role_cannot_read_or_write_another_organization():
    suffix = uuid4().hex
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            organization_a = connection.execute(
                text(
                    """
                    INSERT INTO organizations (name, slug, is_active, created_at)
                    VALUES (:name, :slug, true, now())
                    RETURNING id
                    """
                ),
                {"name": f"RLS A {suffix}", "slug": f"rls-a-{suffix}"},
            ).scalar_one()
            organization_b = connection.execute(
                text(
                    """
                    INSERT INTO organizations (name, slug, is_active, created_at)
                    VALUES (:name, :slug, true, now())
                    RETURNING id
                    """
                ),
                {"name": f"RLS B {suffix}", "slug": f"rls-b-{suffix}"},
            ).scalar_one()
            for organization_id, alert_id in (
                (organization_a, f"rls-a-{suffix}"),
                (organization_b, f"rls-b-{suffix}"),
            ):
                connection.execute(
                    text(
                        """
                        INSERT INTO alerts (
                            organization_id, alert_id, rule_id, rule_name,
                            severity, event_id, event_name, cloud_provider,
                            occurrence_count, status, metadata, created_at,
                            updated_at, first_seen_at, last_seen_at,
                            notification_status
                        ) VALUES (
                            :organization_id, :alert_id, 'rls-test', 'RLS test',
                            'high', :event_id, 'RlsEvent', 'aws',
                            1, 'open', '{}'::json, now(), now(), now(), now(),
                            'pending'
                        )
                        """
                    ),
                    {
                        "organization_id": organization_id,
                        "alert_id": alert_id,
                        "event_id": f"event-{alert_id}",
                    },
                )

            connection.execute(text("SET LOCAL ROLE cloud_security_runtime"))

            assert connection.execute(text("SELECT alert_id FROM alerts")).all() == []

            connection.execute(
                text("SELECT set_config(:setting, :organization_id, true)"),
                {
                    "setting": TENANT_SETTING,
                    "organization_id": str(organization_a),
                },
            )
            visible = connection.execute(
                text("SELECT alert_id FROM alerts ORDER BY alert_id")
            ).scalars().all()
            assert visible == [f"rls-a-{suffix}"]

            savepoint = connection.begin_nested()
            with pytest.raises(DBAPIError):
                connection.execute(
                    text(
                        """
                        INSERT INTO alerts (
                            organization_id, alert_id, rule_id, rule_name,
                            severity, event_id, event_name, cloud_provider,
                            occurrence_count, status, metadata, created_at,
                            updated_at, first_seen_at, last_seen_at,
                            notification_status
                        ) VALUES (
                            :organization_id, :alert_id, 'rls-test', 'blocked',
                            'high', :event_id, 'RlsEvent', 'aws',
                            1, 'open', '{}'::json, now(), now(), now(), now(),
                            'pending'
                        )
                        """
                    ),
                    {
                        "organization_id": organization_b,
                        "alert_id": f"blocked-{suffix}",
                        "event_id": f"blocked-event-{suffix}",
                    },
                )
            savepoint.rollback()
        finally:
            transaction.rollback()
