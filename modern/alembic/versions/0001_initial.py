"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String, nullable=False, unique=True),
        sa.Column('password_hash', sa.String),
        sa.Column('role', sa.String, default='user'),
        sa.Column('display_name', sa.String),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table('profiles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('key', sa.String, nullable=False),
        sa.Column('value', sa.Text),
    )

    op.create_table('projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table('habits',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('cadence', sa.String),
        sa.Column('difficulty', sa.Integer, default=1),
        sa.Column('xp_reward', sa.Integer, default=10),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    op.create_table('logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('habit_id', sa.Integer, sa.ForeignKey('habits.id')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    op.create_table('achievements',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('earned_at', sa.DateTime),
    )

    op.create_table('integrations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String, nullable=False),
        sa.Column('external_id', sa.String),
        sa.Column('config', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    op.create_table('oauth_tokens',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('integration_id', sa.Integer, sa.ForeignKey('integrations.id')),
        sa.Column('access_token', sa.Text),
        sa.Column('refresh_token', sa.Text),
        sa.Column('scope', sa.Text),
        sa.Column('expires_at', sa.Integer),
    )

    op.create_table('change_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer),
        sa.Column('entity', sa.String),
        sa.Column('entity_id', sa.Integer),
        sa.Column('action', sa.String),
        sa.Column('payload', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    op.create_table('guilds',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('owner_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    op.create_table('guild_members',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.Integer, sa.ForeignKey('guilds.id')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('role', sa.String, default='member'),
    )


def downgrade():
    op.drop_table('guild_members')
    op.drop_table('guilds')
    op.drop_table('change_log')
    op.drop_table('oauth_tokens')
    op.drop_table('integrations')
    op.drop_table('achievements')
    op.drop_table('logs')
    op.drop_table('habits')
    op.drop_table('projects')
    op.drop_table('profiles')
    op.drop_table('users')
