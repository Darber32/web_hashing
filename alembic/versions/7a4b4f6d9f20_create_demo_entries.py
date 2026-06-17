"""create demo entries

Revision ID: 7a4b4f6d9f20
Revises: 3c3f9b8e2d41
Create Date: 2026-04-21 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a4b4f6d9f20"
down_revision: Union[str, Sequence[str], None] = "3c3f9b8e2d41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demo_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hash_function", sa.String(), nullable=False),
        sa.Column("collision_method", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("message_bits", sa.Text(), nullable=False),
        sa.Column("hash_value", sa.String(), nullable=False),
        sa.Column("process_note", sa.Text(), nullable=False),
        sa.Column("collision_note", sa.Text(), nullable=False),
        sa.Column("initial_slot", sa.Integer(), nullable=False),
        sa.Column("final_slot", sa.Integer(), nullable=False),
        sa.Column("collision_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("chain_position", sa.Integer(), nullable=True),
        sa.Column("probe_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("step_size", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_demo_entries_id"), "demo_entries", ["id"], unique=False)
    op.create_index(
        "ix_demo_entries_context",
        "demo_entries",
        ["hash_function", "collision_method"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_demo_entries_context", table_name="demo_entries")
    op.drop_index(op.f("ix_demo_entries_id"), table_name="demo_entries")
    op.drop_table("demo_entries")
