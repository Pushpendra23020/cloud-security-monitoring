"""enforce tenant parent-child relationships

Revision ID: d93e00000004
Revises: c82d00000003
"""

from alembic import op


revision = "d93e00000004"
down_revision = "c82d00000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM organization_memberships
                WHERE role NOT IN ('admin', 'analyst', 'viewer')
            ) THEN
                RAISE EXCEPTION 'Tenant relationship migration blocked: invalid organization membership role.';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM assets a
                JOIN cloud_accounts c ON c.id = a.cloud_account_id
                WHERE a.organization_id <> c.organization_id
            ) THEN
                RAISE EXCEPTION 'Tenant relationship migration blocked: asset belongs to a different organization than its cloud account.';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM findings f
                JOIN assets a ON a.id = f.asset_id
                WHERE f.organization_id <> a.organization_id
            ) THEN
                RAISE EXCEPTION 'Tenant relationship migration blocked: finding belongs to a different organization than its asset.';
            END IF;
        END $$;
        """
    )
    op.create_check_constraint(
        "ck_organization_memberships_role",
        "organization_memberships",
        "role IN ('admin', 'analyst', 'viewer')",
    )
    op.create_unique_constraint(
        "uq_cloud_accounts_org_id",
        "cloud_accounts",
        ["organization_id", "id"],
    )
    op.create_unique_constraint(
        "uq_assets_org_id",
        "assets",
        ["organization_id", "id"],
    )
    op.create_foreign_key(
        "fk_assets_org_cloud_account",
        "assets",
        "cloud_accounts",
        ["organization_id", "cloud_account_id"],
        ["organization_id", "id"],
    )
    op.create_foreign_key(
        "fk_findings_org_asset",
        "findings",
        "assets",
        ["organization_id", "asset_id"],
        ["organization_id", "id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_findings_org_asset", "findings", type_="foreignkey")
    op.drop_constraint("fk_assets_org_cloud_account", "assets", type_="foreignkey")
    op.drop_constraint("uq_assets_org_id", "assets", type_="unique")
    op.drop_constraint("uq_cloud_accounts_org_id", "cloud_accounts", type_="unique")
    op.drop_constraint(
        "ck_organization_memberships_role",
        "organization_memberships",
        type_="check",
    )
