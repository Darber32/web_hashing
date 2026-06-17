"""add demo entry owners

Revision ID: a4e7c9b2d113
Revises: 9c7d1e2f4a30
Create Date: 2026-04-21 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4e7c9b2d113"
down_revision: Union[str, Sequence[str], None] = "9c7d1e2f4a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "demo_entries",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "demo_entries",
        sa.Column("guest_token", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_demo_entries_user_id",
        "demo_entries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_demo_entries_guest_token",
        "demo_entries",
        ["guest_token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_demo_entries_guest_token", table_name="demo_entries")
    op.drop_index("ix_demo_entries_user_id", table_name="demo_entries")
    op.drop_column("demo_entries", "guest_token")
    op.drop_column("demo_entries", "user_id")
