"""add immutable event archive metadata

Revision ID: g26b00000007
Revises: f15a00000006
"""

import sqlalchemy as sa
from alembic import op


revision = "g26b00000007"
down_revision = "f15a00000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "security_events",
        sa.Column("archive_uri", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "security_events",
        sa.Column("archive_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "security_events",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "security_events",
        sa.Column(
            "archive_retention_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_security_events_completed_retention",
        "security_events",
        ["status", "processed_at", "archived_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_security_events_completed_retention",
        table_name="security_events",
    )
    op.drop_column("security_events", "archive_retention_until")
    op.drop_column("security_events", "archived_at")
    op.drop_column("security_events", "archive_sha256")
    op.drop_column("security_events", "archive_uri")
