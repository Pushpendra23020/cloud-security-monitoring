"""enrich asset security metadata

Revision ID: 905289aa3f4a
Revises: 9cf39fb4fab8
Create Date: 2026-08-16 17:15:37.881657
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "905289aa3f4a"
down_revision: Union[str, Sequence[str], None] = "9cf39fb4fab8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column(
            "risk_score",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "risk_level",
            sa.String(),
            nullable=False,
            server_default="low",
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "findings_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "alerts_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "public_exposure",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "resource_state",
            sa.String(),
            nullable=False,
            server_default="unknown",
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "tags",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )

    op.add_column(
        "assets",
        sa.Column(
            "last_seen",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.alter_column(
        "assets",
        "cloud_account_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "assets",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "assets",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=True,
    )

    op.alter_column(
        "assets",
        "cloud_account_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.drop_column("assets", "last_seen")
    op.drop_column("assets", "tags")
    op.drop_column("assets", "resource_state")
    op.drop_column("assets", "public_exposure")
    op.drop_column("assets", "alerts_count")
    op.drop_column("assets", "findings_count")
    op.drop_column("assets", "risk_level")
    op.drop_column("assets", "risk_score")
