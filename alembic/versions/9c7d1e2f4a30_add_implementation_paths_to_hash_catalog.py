"""add implementation paths to hash catalog

Revision ID: 9c7d1e2f4a30
Revises: 8f2b6c4d1e90
Create Date: 2026-04-21 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c7d1e2f4a30"
down_revision: Union[str, Sequence[str], None] = "8f2b6c4d1e90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hash_function_options",
        sa.Column(
            "implementation_path",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "collision_method_options",
        sa.Column(
            "implementation_path",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "collision_method_options",
        sa.Column("step_hash_function_code", sa.String(), nullable=True),
    )

    op.execute(
        """
        UPDATE hash_function_options
        SET implementation_path = CASE code
            WHEN 'md5' THEN 'App.services.hashing.hash_functions.MD5_Hash_Function'
            WHEN 'md6' THEN 'App.services.hashing.hash_functions.MD6_Hash_Function'
            WHEN 'sha1' THEN 'App.services.hashing.hash_functions.SHA1_Hash_Function'
            WHEN 'sha256' THEN 'App.services.hashing.hash_functions.SHA256_Hash_Function'
            ELSE implementation_path
        END
        """
    )

    op.execute(
        """
        UPDATE collision_method_options
        SET implementation_path = CASE code
            WHEN 'chaining' THEN 'App.services.hashing.collision_methods.Chaining_Collision_Method'
            WHEN 'double_hashing' THEN 'App.services.hashing.collision_methods.Double_Hashing_Collision_Method'
            ELSE implementation_path
        END
        """
    )

    op.execute(
        """
        UPDATE collision_method_options
        SET step_hash_function_code = 'sha256'
        WHERE code = 'double_hashing'
        """
    )


def downgrade() -> None:
    op.drop_column("collision_method_options", "step_hash_function_code")
    op.drop_column("collision_method_options", "implementation_path")
    op.drop_column("hash_function_options", "implementation_path")
