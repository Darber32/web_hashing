"""create hash catalog and drop demo bits

Revision ID: 8f2b6c4d1e90
Revises: 7a4b4f6d9f20
Create Date: 2026-04-21 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f2b6c4d1e90"
down_revision: Union[str, Sequence[str], None] = "7a4b4f6d9f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hash_function_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        op.f("ix_hash_function_options_id"),
        "hash_function_options",
        ["id"],
        unique=False,
    )

    op.create_table(
        "collision_method_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        op.f("ix_collision_method_options_id"),
        "collision_method_options",
        ["id"],
        unique=False,
    )

    hash_function_options = sa.table(
        "hash_function_options",
        sa.column("code", sa.String()),
        sa.column("label", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_enabled", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    collision_method_options = sa.table(
        "collision_method_options",
        sa.column("code", sa.String()),
        sa.column("label", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_enabled", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )

    op.bulk_insert(
        hash_function_options,
        [
            {
                "code": "md5",
                "label": "MD5",
                "description": "Быстрый алгоритм с 128-битным хешем. Подходит для демонстрации классической схемы вычисления хеша.",
                "is_enabled": True,
                "sort_order": 10,
            },
            {
                "code": "md6",
                "label": "MD6",
                "description": "Учебная аппроксимация MD6. Используется для сравнения поведения таблицы и разрешения коллизий.",
                "is_enabled": True,
                "sort_order": 20,
            },
            {
                "code": "sha1",
                "label": "SHA-1",
                "description": "Алгоритм семейства SHA с 160-битным результатом. Полезен для учебного сравнения старых подходов.",
                "is_enabled": True,
                "sort_order": 30,
            },
            {
                "code": "sha256",
                "label": "SHA-256",
                "description": "Современный алгоритм семейства SHA-2 с 256-битным хешем.",
                "is_enabled": True,
                "sort_order": 40,
            },
        ],
    )

    op.bulk_insert(
        collision_method_options,
        [
            {
                "code": "chaining",
                "label": "Цепочки",
                "description": "При коллизии записи остаются в одной корзине и выстраиваются в цепочку.",
                "is_enabled": True,
                "sort_order": 10,
            },
            {
                "code": "double_hashing",
                "label": "Двойное хеширование",
                "description": "При коллизии используется второй хеш, задающий шаг повторного пробирования.",
                "is_enabled": True,
                "sort_order": 20,
            },
        ],
    )

    op.drop_column("demo_entries", "message_bits")


def downgrade() -> None:
    op.add_column(
        "demo_entries",
        sa.Column(
            "message_bits",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )
    op.drop_index(op.f("ix_collision_method_options_id"), table_name="collision_method_options")
    op.drop_table("collision_method_options")
    op.drop_index(op.f("ix_hash_function_options_id"), table_name="hash_function_options")
    op.drop_table("hash_function_options")
