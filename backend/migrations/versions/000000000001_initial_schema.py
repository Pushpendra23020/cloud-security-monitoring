"""initial database schema

Revision ID: 000000000001
Revises:
Create Date: 2026-08-21

This migration reconstructs the database schema that existed before
Alembic migrations were introduced.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "000000000001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cloud_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id",
            name="cloud_accounts_account_id_key",
        ),
    )
    op.create_index(
        "ix_cloud_accounts_id",
        "cloud_accounts",
        ["id"],
        unique=False,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("user", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cloud_account_id", sa.Integer(), nullable=True),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cloud_account_id"],
            ["cloud_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id"),
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("findings")
    op.drop_table("assets")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_index(
        "ix_cloud_accounts_id",
        table_name="cloud_accounts",
    )
    op.drop_table("cloud_accounts")
