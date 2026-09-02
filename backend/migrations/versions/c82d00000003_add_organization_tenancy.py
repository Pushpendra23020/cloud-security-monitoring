"""add organization tenancy and tenant-safe uniqueness

Revision ID: c82d00000003
Revises: b71c00000002
"""

from alembic import op
import sqlalchemy as sa


revision = "c82d00000003"
down_revision = "b71c00000002"
branch_labels = None
depends_on = None


TENANT_TABLES = ("cloud_accounts", "assets", "findings", "alerts", "incidents", "audit_logs")


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_id", "organizations", ["id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.execute(
        "INSERT INTO organizations (id, name, slug, is_active, created_at) "
        "VALUES (1, 'Default Organization', 'default', true, now())"
    )
    op.execute("SELECT setval(pg_get_serial_sequence('organizations', 'id'), 1, true)")

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_memberships_org_user"),
    )
    op.create_index("ix_organization_memberships_id", "organization_memberships", ["id"])
    op.create_index("ix_organization_memberships_organization_id", "organization_memberships", ["organization_id"])
    op.create_index("ix_organization_memberships_user_id", "organization_memberships", ["user_id"])
    op.create_index("ix_organization_memberships_role", "organization_memberships", ["role"])
    op.execute(
        "INSERT INTO organization_memberships "
        "(organization_id, user_id, role, is_active, created_at) "
        "SELECT 1, id, role, true, now() FROM users"
    )

    for table_name in TENANT_TABLES:
        op.add_column(
            table_name,
            sa.Column("organization_id", sa.Integer(), nullable=True, server_default="1"),
        )
        op.create_foreign_key(
            f"fk_{table_name}_organization_id",
            table_name,
            "organizations",
            ["organization_id"],
            ["id"],
        )
        op.alter_column(table_name, "organization_id", nullable=False, server_default=None)
        op.create_index(f"ix_{table_name}_organization_id", table_name, ["organization_id"])

    op.drop_index("ix_cloud_accounts_account_id", table_name="cloud_accounts")
    op.create_index("ix_cloud_accounts_account_id", "cloud_accounts", ["account_id"])
    op.create_unique_constraint(
        "uq_cloud_accounts_org_account", "cloud_accounts", ["organization_id", "account_id"]
    )

    op.drop_constraint("assets_asset_id_key", "assets", type_="unique")
    op.create_unique_constraint("uq_assets_org_asset", "assets", ["organization_id", "asset_id"])

    op.drop_index("ix_alerts_alert_id", table_name="alerts")
    op.drop_index("ix_alerts_detection_key", table_name="alerts")
    op.create_index("ix_alerts_alert_id", "alerts", ["alert_id"])
    op.create_index("ix_alerts_detection_key", "alerts", ["detection_key"])
    op.create_unique_constraint("uq_alerts_org_alert", "alerts", ["organization_id", "alert_id"])
    op.create_unique_constraint(
        "uq_alerts_org_detection_key", "alerts", ["organization_id", "detection_key"]
    )

    op.drop_index("ix_incidents_incident_id", table_name="incidents")
    op.create_index("ix_incidents_incident_id", "incidents", ["incident_id"])
    op.create_unique_constraint(
        "uq_incidents_org_incident", "incidents", ["organization_id", "incident_id"]
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM cloud_accounts GROUP BY account_id HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Cannot downgrade tenancy: duplicate cloud account IDs exist across organizations.';
            END IF;
            IF EXISTS (SELECT 1 FROM assets GROUP BY asset_id HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Cannot downgrade tenancy: duplicate asset IDs exist across organizations.';
            END IF;
            IF EXISTS (SELECT 1 FROM alerts GROUP BY alert_id HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Cannot downgrade tenancy: duplicate alert IDs exist across organizations.';
            END IF;
            IF EXISTS (
                SELECT 1 FROM alerts
                WHERE detection_key IS NOT NULL
                GROUP BY detection_key HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade tenancy: duplicate alert detection keys exist across organizations.';
            END IF;
            IF EXISTS (SELECT 1 FROM incidents GROUP BY incident_id HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Cannot downgrade tenancy: duplicate incident IDs exist across organizations.';
            END IF;
        END $$;
        """
    )
    op.drop_constraint("uq_incidents_org_incident", "incidents", type_="unique")
    op.drop_index("ix_incidents_incident_id", table_name="incidents")
    op.create_index("ix_incidents_incident_id", "incidents", ["incident_id"], unique=True)

    op.drop_constraint("uq_alerts_org_detection_key", "alerts", type_="unique")
    op.drop_constraint("uq_alerts_org_alert", "alerts", type_="unique")
    op.drop_index("ix_alerts_detection_key", table_name="alerts")
    op.drop_index("ix_alerts_alert_id", table_name="alerts")
    op.create_index("ix_alerts_detection_key", "alerts", ["detection_key"], unique=True)
    op.create_index("ix_alerts_alert_id", "alerts", ["alert_id"], unique=True)

    op.drop_constraint("uq_assets_org_asset", "assets", type_="unique")
    op.create_unique_constraint("assets_asset_id_key", "assets", ["asset_id"])

    op.drop_constraint("uq_cloud_accounts_org_account", "cloud_accounts", type_="unique")
    op.drop_index("ix_cloud_accounts_account_id", table_name="cloud_accounts")
    op.create_index("ix_cloud_accounts_account_id", "cloud_accounts", ["account_id"], unique=True)

    for table_name in reversed(TENANT_TABLES):
        op.drop_index(f"ix_{table_name}_organization_id", table_name=table_name)
        op.drop_constraint(f"fk_{table_name}_organization_id", table_name, type_="foreignkey")
        op.drop_column(table_name, "organization_id")

    op.drop_table("organization_memberships")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_index("ix_organizations_id", table_name="organizations")
    op.drop_table("organizations")
