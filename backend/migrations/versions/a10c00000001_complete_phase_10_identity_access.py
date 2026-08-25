"""complete phase 10 identity and access management

Revision ID: a10c00000001
Revises: 323ba399e501
"""

from alembic import op
import sqlalchemy as sa

revision = "a10c00000001"
down_revision = "323ba399e501"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "username", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "email", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=False)
    op.add_column("users", sa.Column("role", sa.String(30), nullable=False, server_default="analyst"))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.alter_column("audit_logs", "action", existing_type=sa.String(), nullable=False)
    op.alter_column("audit_logs", "user", existing_type=sa.String(), nullable=False)
    op.add_column("audit_logs", sa.Column("method", sa.String(10)))
    op.add_column("audit_logs", sa.Column("path", sa.String(500)))
    op.add_column("audit_logs", sa.Column("status_code", sa.Integer()))
    op.add_column("audit_logs", sa.Column("client_ip", sa.String(64)))
    op.alter_column("audit_logs", "created_at", existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_user", "audit_logs", ["user"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_id", table_name="audit_logs")
    for column in ("client_ip", "status_code", "path", "method"):
        op.drop_column("audit_logs", column)
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    for column in ("last_login_at", "created_at", "is_active", "role"):
        op.drop_column("users", column)
