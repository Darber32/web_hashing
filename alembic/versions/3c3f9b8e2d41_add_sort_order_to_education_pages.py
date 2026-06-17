"""add sort order to education pages

Revision ID: 3c3f9b8e2d41
Revises: b2d6e6f4a1d1
Create Date: 2026-04-20 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c3f9b8e2d41"
down_revision: Union[str, Sequence[str], None] = "b2d6e6f4a1d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "education_pages",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("education_pages", "sort_order")
