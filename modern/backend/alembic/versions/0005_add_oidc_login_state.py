"""add oidc_login_state table

Revision ID: 0005_add_oidc_login_state
Revises: 0004_add_public_tokens
Create Date: 2025-08-28 00:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0005_add_oidc_login_state'
down_revision = '0004_add_public_tokens'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'oidc_login_state',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('state', sa.String(), unique=True, nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('code_verifier', sa.String(), nullable=False),
        sa.Column('redirect_to', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('oidc_login_state')
