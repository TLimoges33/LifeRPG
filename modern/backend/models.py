from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, create_engine, func, UniqueConstraint
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from datetime import datetime

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./modern_dev.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String)
    role = Column(String, default='user')
    display_name = Column(String)
    totp_secret = Column(String)  # base32 secret (encrypted at rest optional)
    totp_enabled = Column(Integer, default=0)  # 0/1
    recovery_codes = Column(Text)  # newline-separated bcrypt hashes
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    profile = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text)

    user = relationship("User", back_populates="profile")

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    user = relationship("User", back_populates="projects")

class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    notes = Column(Text)
    cadence = Column(String)
    difficulty = Column(Integer, default=1)
    xp_reward = Column(Integer, default=10)
    status = Column(String, default='active')  # active|completed|archived
    due_date = Column(DateTime)
    labels = Column(Text)  # JSON list of labels
    created_at = Column(DateTime, server_default=func.current_timestamp())

    user = relationship("User", back_populates="habits")

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String)
    timestamp = Column(DateTime, server_default=func.current_timestamp())

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    earned_at = Column(DateTime)

class Integration(Base):
    __tablename__ = 'integrations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    provider = Column(String, nullable=False)
    external_id = Column(String)
    config = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

class OAuthToken(Base):
    __tablename__ = 'oauth_tokens'
    id = Column(Integer, primary_key=True)
    integration_id = Column(Integer, ForeignKey('integrations.id'))
    access_token = Column(Text)
    refresh_token = Column(Text)
    scope = Column(Text)
    expires_at = Column(Integer)

class ChangeLog(Base):
    __tablename__ = 'change_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    entity = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    payload = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class Guild(Base):
    __tablename__ = 'guilds'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, server_default=func.current_timestamp())


class GuildMember(Base):
    __tablename__ = 'guild_members'
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String, default='member')


class TelemetryEvent(Base):
    __tablename__ = 'telemetry_events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String, nullable=False)
    payload = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class IntegrationItemMap(Base):
    __tablename__ = 'integration_item_map'
    id = Column(Integer, primary_key=True)
    integration_id = Column(Integer, ForeignKey('integrations.id'), nullable=False)
    external_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        UniqueConstraint('integration_id', 'external_id', 'entity_type', name='uq_integration_item'),
    )


class PublicToken(Base):
    __tablename__ = 'public_tokens'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    scope = Column(String, default='read:widgets')
    token_hash = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    last_used_at = Column(DateTime)


class OIDCLoginState(Base):
    __tablename__ = 'oidc_login_state'
    id = Column(Integer, primary_key=True)
    state = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)
    code_verifier = Column(String, nullable=False)
    redirect_to = Column(String)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    expires_at = Column(DateTime)


def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    init_db()
    print('Initialized DB ->', DATABASE_URL)
