"""Ununique username, rename email_token, add token_expiry and new_email

Revision ID: 1b8154d577bf
Revises: 1f769523f4ef
Create Date: 2026-03-14 15:03:32.187344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b8154d577bf'
down_revision: Union[str, Sequence[str], None] = '1f769523f4ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint('users_username_key', 'users', type_='unique')
    op.alter_column('users', 'email_token', new_column_name='token')
    op.add_column('users', sa.Column('token_expiry', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('new_email', sa.String(), nullable=True))


def downgrade():
    op.create_unique_constraint('users_username_key', 'users', ['username'])
    op.drop_column('users', 'new_email')
    op.drop_column('users', 'token_expiry')
    op.alter_column('users', 'token', new_column_name='email_token')
