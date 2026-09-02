"""add MFA, OIDC identities and distributed authentication rate limits

Revision ID: i48d00000009
Revises: h37c00000008
"""

import sqlalchemy as sa
from alembic import op


revision = "i48d00000009"
down_revision = "h37c00000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("mfa_last_used_step", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("oidc_issuer", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("oidc_subject", sa.String(length=255), nullable=True))
    op.create_index(
        "uq_users_oidc_identity",
        "users",
        ["oidc_issuer", "oidc_subject"],
        unique=True,
    )

    op.create_table(
        "mfa_recovery_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_hash"),
    )
    op.create_index(
        "ix_mfa_recovery_codes_user_id",
        "mfa_recovery_codes",
        ["user_id"],
    )
    op.create_index(
        "ix_mfa_recovery_codes_used_at",
        "mfa_recovery_codes",
        ["used_at"],
    )

    op.create_table(
        "mfa_challenges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mfa_challenges_user_id", "mfa_challenges", ["user_id"])
    op.create_index("ix_mfa_challenges_expires_at", "mfa_challenges", ["expires_at"])
    op.create_index("ix_mfa_challenges_consumed_at", "mfa_challenges", ["consumed_at"])

    op.create_table(
        "auth_rate_limits",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "window_started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index("ix_auth_rate_limits_scope", "auth_rate_limits", ["scope"])
    op.create_index(
        "ix_auth_rate_limits_blocked_until",
        "auth_rate_limits",
        ["blocked_until"],
    )


def downgrade() -> None:
    op.drop_index("ix_auth_rate_limits_blocked_until", table_name="auth_rate_limits")
    op.drop_index("ix_auth_rate_limits_scope", table_name="auth_rate_limits")
    op.drop_table("auth_rate_limits")
    op.drop_index("ix_mfa_challenges_consumed_at", table_name="mfa_challenges")
    op.drop_index("ix_mfa_challenges_expires_at", table_name="mfa_challenges")
    op.drop_index("ix_mfa_challenges_user_id", table_name="mfa_challenges")
    op.drop_table("mfa_challenges")
    op.drop_index("ix_mfa_recovery_codes_used_at", table_name="mfa_recovery_codes")
    op.drop_index("ix_mfa_recovery_codes_user_id", table_name="mfa_recovery_codes")
    op.drop_table("mfa_recovery_codes")
    op.drop_index("uq_users_oidc_identity", table_name="users")
    op.drop_column("users", "oidc_subject")
    op.drop_column("users", "oidc_issuer")
    op.drop_column("users", "mfa_last_used_step")
    op.drop_column("users", "mfa_secret_encrypted")
    op.drop_column("users", "mfa_enabled")
