"""add public_tokens table

Revision ID: 0004_add_public_tokens
Revises: 0002_add_habit_fields
Create Date: 2025-08-28 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_add_public_tokens'
down_revision = '0002_add_habit_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'public_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), server_default='read:widgets'),
        sa.Column('token_hash', sa.String(), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('public_tokens')
