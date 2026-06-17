"""add collision state to compare entries

Revision ID: c4a62b8ef31d
Revises: b8d4c1a7e291
Create Date: 2026-04-22 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4a62b8ef31d"
down_revision: Union[str, Sequence[str], None] = "b8d4c1a7e291"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compare_entries",
        sa.Column(
            "collision_method",
            sa.String(),
            nullable=False,
            server_default="chaining",
        ),
    )
    op.create_index(
        "ix_compare_entries_collision_method",
        "compare_entries",
        ["collision_method"],
        unique=False,
    )

    op.add_column(
        "compare_results",
        sa.Column(
            "collision_note",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "compare_results",
        sa.Column(
            "initial_slot",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "compare_results",
        sa.Column(
            "final_slot",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "compare_results",
        sa.Column(
            "collision_detected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "compare_results",
        sa.Column("chain_position", sa.Integer(), nullable=True),
    )
    op.add_column(
        "compare_results",
        sa.Column(
            "probe_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "compare_results",
        sa.Column("step_size", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("compare_results", "step_size")
    op.drop_column("compare_results", "probe_count")
    op.drop_column("compare_results", "chain_position")
    op.drop_column("compare_results", "collision_detected")
    op.drop_column("compare_results", "final_slot")
    op.drop_column("compare_results", "initial_slot")
    op.drop_column("compare_results", "collision_note")

    op.drop_index(
        "ix_compare_entries_collision_method",
        table_name="compare_entries",
    )
    op.drop_column("compare_entries", "collision_method")
