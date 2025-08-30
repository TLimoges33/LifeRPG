"""add status/due_date/labels to habit

Revision ID: 0002_add_habit_fields
Revises: 0001_add_integration_item_map
Create Date: 2025-08-28 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_habit_fields'
down_revision = '0001_add_integration_item_map'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('habits', sa.Column('status', sa.String(), server_default='active'))
    op.add_column('habits', sa.Column('due_date', sa.DateTime(), nullable=True))
    op.add_column('habits', sa.Column('labels', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('habits', 'labels')
    op.drop_column('habits', 'due_date')
    op.drop_column('habits', 'status')
