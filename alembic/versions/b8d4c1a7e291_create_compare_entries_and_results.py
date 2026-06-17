"""create compare entries and results

Revision ID: b8d4c1a7e291
Revises: a4e7c9b2d113
Create Date: 2026-04-22 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8d4c1a7e291"
down_revision: Union[str, Sequence[str], None] = "a4e7c9b2d113"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compare_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("guest_token", sa.String(), nullable=True),
        sa.Column("selection_key", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compare_entries_id", "compare_entries", ["id"], unique=False)
    op.create_index(
        "ix_compare_entries_user_id",
        "compare_entries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_compare_entries_guest_token",
        "compare_entries",
        ["guest_token"],
        unique=False,
    )
    op.create_index(
        "ix_compare_entries_selection_key",
        "compare_entries",
        ["selection_key"],
        unique=False,
    )

    op.create_table(
        "compare_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("compare_entry_id", sa.Integer(), nullable=False),
        sa.Column("hash_function", sa.String(), nullable=False),
        sa.Column("hash_label", sa.String(), nullable=False),
        sa.Column("hash_value", sa.String(), nullable=False),
        sa.Column("process_note", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["compare_entry_id"],
            ["compare_entries.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compare_results_id", "compare_results", ["id"], unique=False)
    op.create_index(
        "ix_compare_results_compare_entry_id",
        "compare_results",
        ["compare_entry_id"],
        unique=False,
    )
    op.create_index(
        "ix_compare_results_hash_function",
        "compare_results",
        ["hash_function"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_compare_results_hash_function", table_name="compare_results")
    op.drop_index("ix_compare_results_compare_entry_id", table_name="compare_results")
    op.drop_index("ix_compare_results_id", table_name="compare_results")
    op.drop_table("compare_results")

    op.drop_index("ix_compare_entries_selection_key", table_name="compare_entries")
    op.drop_index("ix_compare_entries_guest_token", table_name="compare_entries")
    op.drop_index("ix_compare_entries_user_id", table_name="compare_entries")
    op.drop_index("ix_compare_entries_id", table_name="compare_entries")
    op.drop_table("compare_entries")
