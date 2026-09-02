"""add durable tenant event queue

Revision ID: f15a00000006
Revises: e04f00000005
"""

import sqlalchemy as sa
from alembic import op


revision = "f15a00000006"
down_revision = "e04f00000005"
branch_labels = None
depends_on = None


POLICY_NAME = "organization_tenant_isolation"
TENANT_EXPRESSION = (
    "organization_id = "
    "NULLIF(current_setting('app.current_organization_id', true), '')::INTEGER"
)


def upgrade() -> None:
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("raw_event", sa.JSON(), nullable=False),
        sa.Column("normalized_event", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=255), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempts >= 0", name="ck_security_events_attempts"),
        sa.CheckConstraint("max_attempts > 0", name="ck_security_events_max_attempts"),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'retry', 'completed', 'dead_letter')",
            name="ck_security_events_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "event_id",
            name="uq_security_events_org_event",
        ),
    )
    op.create_index(
        "ix_security_events_event_id",
        "security_events",
        ["event_id"],
    )
    op.create_index(
        "ix_security_events_organization_id",
        "security_events",
        ["organization_id"],
    )
    op.create_index(
        "ix_security_events_org_queue",
        "security_events",
        ["organization_id", "status", "available_at", "received_at"],
    )
    op.execute('ALTER TABLE "security_events" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "security_events" FORCE ROW LEVEL SECURITY')
    op.execute(
        f"""
        CREATE POLICY {POLICY_NAME} ON "security_events"
        FOR ALL
        USING ({TENANT_EXPRESSION})
        WITH CHECK ({TENANT_EXPRESSION})
        """
    )


def downgrade() -> None:
    op.execute(
        f'DROP POLICY IF EXISTS {POLICY_NAME} ON "security_events"'
    )
    op.execute('ALTER TABLE "security_events" NO FORCE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "security_events" DISABLE ROW LEVEL SECURITY')
    op.drop_index("ix_security_events_org_queue", table_name="security_events")
    op.drop_index("ix_security_events_organization_id", table_name="security_events")
    op.drop_index("ix_security_events_event_id", table_name="security_events")
    op.drop_table("security_events")
