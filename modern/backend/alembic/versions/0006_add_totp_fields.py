"""add totp fields to users

Revision ID: 0006_add_totp_fields
Revises: 0005_add_oidc_login_state
Create Date: 2025-08-28 01:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0006_add_totp_fields'
down_revision = '0005_add_oidc_login_state'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('totp_secret', sa.String(), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Integer(), server_default='0'))
    op.add_column('users', sa.Column('recovery_codes', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('users', 'recovery_codes')
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')
