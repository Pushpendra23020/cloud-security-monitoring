"""enforce tenant row-level security

Revision ID: e04f00000005
Revises: d93e00000004
"""

from alembic import op


revision = "e04f00000005"
down_revision = "d93e00000004"
branch_labels = None
depends_on = None


TENANT_TABLES = (
    "cloud_accounts",
    "assets",
    "findings",
    "alerts",
    "incidents",
    "audit_logs",
)
POLICY_NAME = "organization_tenant_isolation"
TENANT_EXPRESSION = (
    "organization_id = "
    "NULLIF(current_setting('app.current_organization_id', true), '')::INTEGER"
)


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f"""
            CREATE POLICY {POLICY_NAME} ON "{table}"
            FOR ALL
            USING ({TENANT_EXPRESSION})
            WITH CHECK ({TENANT_EXPRESSION})
            """
        )


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.execute(f'DROP POLICY IF EXISTS {POLICY_NAME} ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
