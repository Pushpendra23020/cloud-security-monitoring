"""secure AWS account onboarding metadata

Revision ID: b71c00000002
Revises: a10c00000001
"""
from alembic import op
import sqlalchemy as sa

revision = "b71c00000002"
down_revision = "a10c00000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cloud_accounts", sa.Column("name", sa.String(120), nullable=False, server_default="AWS Account"))
    op.add_column("cloud_accounts", sa.Column("auth_method", sa.String(30), nullable=False, server_default="assume_role"))
    op.add_column("cloud_accounts", sa.Column("role_arn", sa.String(2048), nullable=True))
    op.add_column("cloud_accounts", sa.Column("external_id", sa.String(255), nullable=True))
    op.add_column("cloud_accounts", sa.Column("monitoring_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("cloud_accounts", sa.Column("services", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("cloud_accounts", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("cloud_accounts", sa.Column("health_status", sa.String(30), nullable=False, server_default="pending"))
    op.add_column("cloud_accounts", sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for column in ("last_sync", "health_status", "description", "services", "monitoring_enabled", "external_id", "role_arn", "auth_method", "name"):
        op.drop_column("cloud_accounts", column)
