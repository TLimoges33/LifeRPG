"""add integration item map with unique constraint

Revision ID: 0001_add_integration_item_map
Revises: 
Create Date: 2025-08-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_integration_item_map'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'integration_item_map',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('integration_id', 'external_id', 'entity_type', name='uq_integration_item'),
    )


def downgrade():
    op.drop_table('integration_item_map')
