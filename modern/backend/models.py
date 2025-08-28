from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, create_engine, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./modern_dev.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String)
    display_name = Column(String)
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


def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    init_db()
    print('Initialized DB ->', DATABASE_URL)
