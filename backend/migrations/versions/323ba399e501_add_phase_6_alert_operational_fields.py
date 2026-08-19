"""add phase 6 alert operational fields

Revision ID: 323ba399e501
Revises: c5b3a6a4d822
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "323ba399e501"
down_revision = "c5b3a6a4d822"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column(
            "fingerprint",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_alerts_fingerprint"),
        "alerts",
        ["fingerprint"],
        unique=False,
    )

    op.add_column(
        "alerts",
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "notification_status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
    )

    op.create_index(
        op.f("ix_alerts_notification_status"),
        "alerts",
        ["notification_status"],
        unique=False,
    )

    op.add_column(
        "alerts",
        sa.Column(
            "last_notified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "suppressed_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE alerts
        SET
            first_seen_at = created_at,
            last_seen_at = updated_at
        WHERE
            first_seen_at IS NULL
            OR last_seen_at IS NULL
        """
    )

    op.alter_column(
        "alerts",
        "first_seen_at",
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "last_seen_at",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column(
        "alerts",
        "suppressed_until",
    )

    op.drop_column(
        "alerts",
        "last_notified_at",
    )

    op.drop_index(
        op.f("ix_alerts_notification_status"),
        table_name="alerts",
    )

    op.drop_column(
        "alerts",
        "notification_status",
    )

    op.drop_column(
        "alerts",
        "last_seen_at",
    )

    op.drop_column(
        "alerts",
        "first_seen_at",
    )

    op.drop_column(
        "alerts",
        "occurrence_count",
    )

    op.drop_index(
        op.f("ix_alerts_fingerprint"),
        table_name="alerts",
    )

    op.drop_column(
        "alerts",
        "fingerprint",
    )
