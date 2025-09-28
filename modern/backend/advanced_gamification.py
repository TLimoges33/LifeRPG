"""
Advanced Gamification System - Dynamic Quests, Guilds, and Seasonal Events
Provides deep RPG mechanics with adaptive content and social features
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import uuid

from .models import User, Habit, Log
from .db import get_db


class QuestType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    EPIC = "epic"
    SEASONAL = "seasonal"
    GUILD = "guild"


class QuestDifficulty(Enum):
    NOVICE = 1
    ADEPT = 2
    EXPERT = 3
    MASTER = 4
    LEGENDARY = 5


class QuestStatus(Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class GuildRole(Enum):
    MEMBER = "member"
    OFFICER = "officer"
    LEADER = "leader"
    FOUNDER = "founder"


@dataclass
class Quest:
    """Dynamic quest with adaptive requirements"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty
    requirements: Dict[str, Any]
    rewards: Dict[str, Any]
    status: QuestStatus
    created_at: datetime
    expires_at: Optional[datetime]
    progress: Dict[str, Any]
    user_id: Optional[int] = None
    guild_id: Optional[int] = None


@dataclass
class Guild:
    """Player guild with shared goals and benefits"""
    id: int
    name: str
    description: str
    emblem_url: str
    level: int
    experience: int
    member_count: int
    max_members: int
    created_at: datetime
    founder_id: int
    guild_type: str  # casual, competitive, specialized
    perks: Dict[str, Any]
    requirements: Dict[str, Any]


@dataclass
class Achievement:
    """Advanced achievement with tiers and progression"""
    id: str
    title: str
    description: str
    category: str
    tier: int  # 1-5, bronze to legendary
    points: int
    requirements: Dict[str, Any]
    unlocked_at: Optional[datetime]
    progress: Dict[str, Any]
    secret: bool = False
    prerequisites: List[str] = None


@dataclass
class SeasonalEvent:
    """Time-limited seasonal events with special rewards"""
    id: str
    name: str
    theme: str
    description: str
    start_date: datetime
    end_date: datetime
    special_quests: List[str]
    special_rewards: Dict[str, Any]
    participation_requirements: Dict[str, Any]
    leaderboard: Dict[str, Any]


class QuestGenerator:
    """Generates dynamic quests based on user behavior and preferences"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.quest_templates = self._load_quest_templates()
    
    def _load_quest_templates(self) -> Dict[str, Dict]:
        """Load quest templates with dynamic parameters"""
        return {
            "habit_streak": {
                "title_templates": [
                    "Streak Master: Maintain {habit_name} for {days} days",
                    "Consistency Challenge: {days}-day {habit_name} streak",
                    "The Long Road: Build a {days}-day {habit_name} habit"
                ],
                "description_templates": [
                    "Prove your dedication by maintaining your {habit_name} habit for {days} consecutive days.",
                    "Test your consistency with a {days}-day streak of {habit_name}."
                ],
                "requirements": {
                    "streak_days": {"min": 3, "max": 30},
                    "habit_categories": ["fitness", "wellness", "productivity", "learning"]
                },
                "rewards": {
                    "experience": {"base": 50, "multiplier": 10},
                    "coins": {"base": 25, "multiplier": 5},
                    "titles": ["Streak Seeker", "Consistency King", "Habit Master"]
                }
            },
            "habit_variety": {
                "title_templates": [
                    "Renaissance Soul: Complete habits in {categories} different categories",
                    "Jack of All Trades: Master {categories} habit categories",
                    "Diverse Development: Explore {categories} areas of growth"
                ],
                "description_templates": [
                    "Expand your horizons by completing habits across {categories} different categories.",
                    "Show your versatility by maintaining habits in {categories} distinct areas."
                ],
                "requirements": {
                    "category_count": {"min": 3, "max": 8},
                    "completions_per_category": {"min": 3, "max": 10}
                },
                "rewards": {
                    "experience": {"base": 75, "multiplier": 25},
                    "special_items": ["Versatility Badge", "Renaissance Ring"],
                    "unlocks": ["habit_category_bonus"]
                }
            },
            "social_engagement": {
                "title_templates": [
                    "Community Builder: Help {count} guild members with their habits",
                    "Mentor Mode: Guide {count} fellow adventurers",
                    "Support Network: Encourage {count} habit buddies"
                ],
                "description_templates": [
                    "Strengthen the community by supporting {count} other members in their habit journeys.",
                    "Become a beacon of encouragement for {count} fellow habit heroes."
                ],
                "requirements": {
                    "support_count": {"min": 3, "max": 15},
                    "actions": ["comment", "like", "encourage", "share_tip"]
                },
                "rewards": {
                    "experience": {"base": 40, "multiplier": 15},
                    "social_points": {"base": 100, "multiplier": 20},
                    "titles": ["Community Helper", "Mentor", "Support Pillar"]
                }
            },
            "challenge_completion": {
                "title_templates": [
                    "Challenge Conqueror: Complete {count} community challenges",
                    "Rising to the Occasion: Finish {count} challenges successfully",
                    "Challenge Accepted: Excel in {count} different challenges"
                ],
                "description_templates": [
                    "Prove your mettle by successfully completing {count} community challenges.",
                    "Rise above the competition by finishing {count} challenges with excellence."
                ],
                "requirements": {
                    "challenge_count": {"min": 2, "max": 8},
                    "performance_threshold": 0.8  # Top 80% performance required
                },
                "rewards": {
                    "experience": {"base": 100, "multiplier": 30},
                    "challenge_tokens": {"base": 5, "multiplier": 2},
                    "special_titles": ["Challenge Champion", "Contest Crusher"]
                }
            }
        }
    
    async def generate_daily_quests(self, user_id: int, count: int = 3) -> List[Quest]:
        """Generate personalized daily quests for a user"""
        
        user_data = await self._get_user_profile(user_id)
        user_habits = await self._get_user_habits(user_id)
        
        quests = []
        
        # Generate variety of quest types
        quest_types = ["habit_streak", "habit_variety", "social_engagement"]
        selected_types = random.sample(quest_types, min(count, len(quest_types)))
        
        for quest_type in selected_types:
            quest = await self._generate_quest_from_template(
                quest_type, user_data, user_habits, QuestType.DAILY
            )
            if quest:
                quests.append(quest)
        
        return quests
    
    async def generate_weekly_quests(self, user_id: int) -> List[Quest]:
        """Generate challenging weekly quests"""
        
        user_data = await self._get_user_profile(user_id)
        user_habits = await self._get_user_habits(user_id)
        
        # Weekly quests are more challenging
        template = self.quest_templates["challenge_completion"]
        
        quest = Quest(
            id=str(uuid.uuid4()),
            title=random.choice(template["title_templates"]).format(count=3),
            description=random.choice(template["description_templates"]).format(count=3),
            quest_type=QuestType.WEEKLY,
            difficulty=self._calculate_quest_difficulty(user_data),
            requirements={
                "challenge_count": 3,
                "performance_threshold": 0.7,
                "timeframe_days": 7
            },
            rewards={
                "experience": 200,
                "coins": 100,
                "special_reward": "Weekly Champion Badge"
            },
            status=QuestStatus.AVAILABLE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            progress={},
            user_id=user_id
        )
        
        return [quest]
    
    async def generate_guild_quest(self, guild_id: int, guild_data: Dict) -> Quest:
        """Generate a quest for an entire guild"""
        
        # Guild quests require collective effort
        member_count = guild_data["member_count"]
        guild_level = guild_data["level"]
        
        # Scale quest difficulty with guild size and level
        target_completions = max(member_count * 2, 10)
        target_categories = min(3 + (guild_level // 2), 8)
        
        quest = Quest(
            id=str(uuid.uuid4()),
            title=f"Guild Unity: Complete {target_completions} habits across {target_categories} categories",
            description=f"Work together as a guild to complete {target_completions} habits across {target_categories} different categories within the week.",
            quest_type=QuestType.GUILD,
            difficulty=QuestDifficulty.EXPERT,
            requirements={
                "total_completions": target_completions,
                "category_count": target_categories,
                "timeframe_days": 7,
                "min_participation": int(member_count * 0.6)  # 60% participation required
            },
            rewards={
                "guild_experience": 500 + (guild_level * 50),
                "guild_coins": 200 + (guild_level * 20),
                "member_rewards": {
                    "experience": 100,
                    "coins": 50,
                    "guild_tokens": 10
                },
                "guild_perks": ["XP Boost", "Quest Refresh", "Special Emblem"]
            },
            status=QuestStatus.AVAILABLE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            progress={"completions": 0, "categories": set(), "participants": set()},
            guild_id=guild_id
        )
        
        return quest
    
    async def _generate_quest_from_template(self, template_name: str, user_data: Dict, 
                                          user_habits: List[Dict], quest_type: QuestType) -> Optional[Quest]:
        """Generate a quest from a template with personalized parameters"""
        
        template = self.quest_templates.get(template_name)
        if not template:
            return None
        
        # Personalize quest parameters based on user data
        if template_name == "habit_streak":
            # Find user's most consistent habit for streak quest
            best_habit = max(user_habits, key=lambda h: h.get("current_streak", 0)) if user_habits else None
            if not best_habit:
                return None
            
            difficulty = self._calculate_quest_difficulty(user_data)
            streak_days = template["requirements"]["streak_days"]["min"] + (difficulty.value * 2)
            
            quest = Quest(
                id=str(uuid.uuid4()),
                title=random.choice(template["title_templates"]).format(
                    habit_name=best_habit["title"], days=streak_days
                ),
                description=random.choice(template["description_templates"]).format(
                    habit_name=best_habit["title"], days=streak_days
                ),
                quest_type=quest_type,
                difficulty=difficulty,
                requirements={
                    "habit_id": best_habit["id"],
                    "streak_days": streak_days,
                    "consecutive": True
                },
                rewards={
                    "experience": template["rewards"]["experience"]["base"] + 
                                (streak_days * template["rewards"]["experience"]["multiplier"]),
                    "coins": template["rewards"]["coins"]["base"] + 
                           (streak_days * template["rewards"]["coins"]["multiplier"]),
                    "title": random.choice(template["rewards"]["titles"])
                },
                status=QuestStatus.AVAILABLE,
                created_at=datetime.now(),
                expires_at=self._calculate_expiry(quest_type),
                progress={"current_streak": 0, "target_streak": streak_days},
                user_id=user_data["user_id"]
            )
            
            return quest
        
        return None
    
    async def _get_user_profile(self, user_id: int) -> Dict:
        """Get user profile data for quest generation"""
        
        query = """
        SELECT 
            u.id as user_id,
            u.level,
            u.experience,
            u.created_at,
            COUNT(h.id) as habit_count,
            AVG(CASE WHEN l.action = 'completed' THEN 1.0 ELSE 0.0 END) as completion_rate
        FROM users u
        LEFT JOIN habits h ON u.id = h.user_id
        LEFT JOIN logs l ON h.id = l.habit_id AND l.timestamp >= :week_ago
        WHERE u.id = :user_id
        GROUP BY u.id, u.level, u.experience, u.created_at
        """
        
        week_ago = datetime.now() - timedelta(days=7)
        result = await self.db.execute(text(query), {
            "user_id": user_id,
            "week_ago": week_ago
        })
        
        row = result.first()
        if row:
            return {
                "user_id": row.user_id,
                "level": row.level or 1,
                "experience": row.experience or 0,
                "habit_count": row.habit_count or 0,
                "completion_rate": float(row.completion_rate or 0),
                "account_age_days": (datetime.now() - row.created_at).days
            }
        
        return {"user_id": user_id, "level": 1, "experience": 0, "habit_count": 0, 
                "completion_rate": 0.0, "account_age_days": 0}
    
    async def _get_user_habits(self, user_id: int) -> List[Dict]:
        """Get user's habits for quest generation"""
        
        query = """
        SELECT 
            h.id,
            h.title,
            h.category,
            h.difficulty,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions,
            MAX(l.timestamp) as last_completion
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id
        WHERE h.user_id = :user_id AND h.status = 'active'
        GROUP BY h.id, h.title, h.category, h.difficulty
        ORDER BY completions DESC
        """
        
        result = await self.db.execute(text(query), {"user_id": user_id})
        
        habits = []
        for row in result:
            habits.append({
                "id": row.id,
                "title": row.title,
                "category": row.category or "general",
                "difficulty": row.difficulty,
                "completions": row.completions or 0,
                "last_completion": row.last_completion,
                "current_streak": await self._calculate_habit_streak(row.id)
            })
        
        return habits
    
    async def _calculate_habit_streak(self, habit_id: int) -> int:
        """Calculate current streak for a habit"""
        
        query = """
        WITH daily_completions AS (
            SELECT DATE(timestamp) as completion_date
            FROM logs 
            WHERE habit_id = :habit_id AND action = 'completed'
            ORDER BY completion_date DESC
        ),
        streak_calc AS (
            SELECT 
                completion_date,
                completion_date - INTERVAL '1 day' * (ROW_NUMBER() OVER (ORDER BY completion_date DESC) - 1) as expected_date
            FROM daily_completions
        )
        SELECT COUNT(*) as streak
        FROM streak_calc
        WHERE completion_date = expected_date
        """
        
        result = await self.db.execute(text(query), {"habit_id": habit_id})
        row = result.first()
        return row.streak if row else 0
    
    def _calculate_quest_difficulty(self, user_data: Dict) -> QuestDifficulty:
        """Calculate appropriate quest difficulty for user"""
        
        level = user_data["level"]
        completion_rate = user_data["completion_rate"]
        account_age = user_data["account_age_days"]
        
        # Base difficulty on user level
        if level >= 20 and completion_rate > 0.8:
            return QuestDifficulty.LEGENDARY
        elif level >= 15 and completion_rate > 0.7:
            return QuestDifficulty.MASTER
        elif level >= 10 and completion_rate > 0.6:
            return QuestDifficulty.EXPERT
        elif level >= 5 and completion_rate > 0.4:
            return QuestDifficulty.ADEPT
        else:
            return QuestDifficulty.NOVICE
    
    def _calculate_expiry(self, quest_type: QuestType) -> datetime:
        """Calculate when a quest expires"""
        
        expiry_map = {
            QuestType.DAILY: timedelta(hours=24),
            QuestType.WEEKLY: timedelta(days=7),
            QuestType.MONTHLY: timedelta(days=30),
            QuestType.EPIC: timedelta(days=14),
            QuestType.SEASONAL: timedelta(days=90),
            QuestType.GUILD: timedelta(days=7)
        }
        
        return datetime.now() + expiry_map.get(quest_type, timedelta(days=1))


class GuildManager:
    """Manages guild operations and social features"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_guild(self, founder_id: int, guild_data: Dict) -> Guild:
        """Create a new guild"""
        
        query = """
        INSERT INTO guilds (name, description, emblem_url, level, experience,
                           max_members, created_at, founder_id, guild_type,
                           perks, requirements)
        VALUES (:name, :description, :emblem_url, 1, 0, :max_members,
                :created_at, :founder_id, :guild_type, :perks, :requirements)
        RETURNING id
        """
        
        result = await self.db.execute(text(query), {
            "name": guild_data["name"],
            "description": guild_data["description"],
            "emblem_url": guild_data.get("emblem_url", ""),
            "max_members": guild_data.get("max_members", 50),
            "created_at": datetime.now(),
            "founder_id": founder_id,
            "guild_type": guild_data.get("guild_type", "casual"),
            "perks": json.dumps({}),
            "requirements": json.dumps(guild_data.get("requirements", {}))
        })
        
        guild_id = result.scalar()
        
        # Add founder as leader
        await self._add_guild_member(guild_id, founder_id, GuildRole.FOUNDER)
        
        return await self.get_guild(guild_id)
    
    async def get_guild(self, guild_id: int) -> Optional[Guild]:
        """Get guild information"""
        
        query = """
        SELECT g.*, COUNT(gm.user_id) as member_count
        FROM guilds g
        LEFT JOIN guild_members gm ON g.id = gm.guild_id
        WHERE g.id = :guild_id
        GROUP BY g.id
        """
        
        result = await self.db.execute(text(query), {"guild_id": guild_id})
        row = result.first()
        
        if not row:
            return None
        
        return Guild(
            id=row.id,
            name=row.name,
            description=row.description,
            emblem_url=row.emblem_url or "",
            level=row.level,
            experience=row.experience,
            member_count=row.member_count or 0,
            max_members=row.max_members,
            created_at=row.created_at,
            founder_id=row.founder_id,
            guild_type=row.guild_type,
            perks=json.loads(row.perks or '{}'),
            requirements=json.loads(row.requirements or '{}')
        )
    
    async def join_guild(self, guild_id: int, user_id: int) -> bool:
        """Join a guild"""
        
        guild = await self.get_guild(guild_id)
        if not guild:
            return False
        
        # Check if guild is full
        if guild.member_count >= guild.max_members:
            return False
        
        # Check if user meets requirements
        if not await self._check_guild_requirements(user_id, guild.requirements):
            return False
        
        await self._add_guild_member(guild_id, user_id, GuildRole.MEMBER)
        return True
    
    async def _add_guild_member(self, guild_id: int, user_id: int, role: GuildRole):
        """Add a member to a guild"""
        
        query = """
        INSERT INTO guild_members (guild_id, user_id, role, joined_at)
        VALUES (:guild_id, :user_id, :role, :joined_at)
        ON CONFLICT (guild_id, user_id) DO NOTHING
        """
        
        await self.db.execute(text(query), {
            "guild_id": guild_id,
            "user_id": user_id,
            "role": role.value,
            "joined_at": datetime.now()
        })
    
    async def _check_guild_requirements(self, user_id: int, requirements: Dict) -> bool:
        """Check if user meets guild requirements"""
        
        if not requirements:
            return True
        
        # Get user stats
        query = """
        SELECT 
            u.level,
            u.experience,
            COUNT(h.id) as habit_count
        FROM users u
        LEFT JOIN habits h ON u.id = h.user_id
        WHERE u.id = :user_id
        GROUP BY u.id, u.level, u.experience
        """
        
        result = await self.db.execute(text(query), {"user_id": user_id})
        row = result.first()
        
        if not row:
            return False
        
        # Check requirements
        if requirements.get("min_level", 0) > (row.level or 0):
            return False
        
        if requirements.get("min_experience", 0) > (row.experience or 0):
            return False
        
        if requirements.get("min_habits", 0) > (row.habit_count or 0):
            return False
        
        return True
    
    async def get_guild_members(self, guild_id: int) -> List[Dict]:
        """Get guild members with their stats"""
        
        query = """
        SELECT 
            gm.user_id,
            gm.role,
            gm.joined_at,
            u.username,
            u.level,
            u.experience,
            COUNT(h.id) as habit_count
        FROM guild_members gm
        JOIN users u ON gm.user_id = u.id
        LEFT JOIN habits h ON u.id = h.user_id
        WHERE gm.guild_id = :guild_id
        GROUP BY gm.user_id, gm.role, gm.joined_at, u.username, u.level, u.experience
        ORDER BY 
            CASE gm.role 
                WHEN 'founder' THEN 1
                WHEN 'leader' THEN 2  
                WHEN 'officer' THEN 3
                ELSE 4
            END,
            gm.joined_at
        """
        
        result = await self.db.execute(text(query), {"guild_id": guild_id})
        
        members = []
        for row in result:
            members.append({
                "user_id": row.user_id,
                "username": row.username,
                "role": row.role,
                "level": row.level or 1,
                "experience": row.experience or 0,
                "habit_count": row.habit_count or 0,
                "joined_at": row.joined_at
            })
        
        return members


class SeasonalEventManager:
    """Manages seasonal events and limited-time content"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.seasonal_events = self._load_seasonal_events()
    
    def _load_seasonal_events(self) -> Dict[str, Dict]:
        """Load seasonal event templates"""
        return {
            "new_year_resolution": {
                "name": "New Year, New You",
                "theme": "fresh_start",
                "duration_days": 31,
                "special_rewards": {
                    "resolution_keeper": {
                        "experience": 1000,
                        "title": "Resolution Keeper",
                        "special_item": "New Year Crown"
                    }
                },
                "special_quests": [
                    {
                        "title": "Fresh Start Challenge",
                        "description": "Start 3 new habits and maintain them for 21 days",
                        "requirements": {"new_habits": 3, "streak_days": 21}
                    }
                ]
            },
            "summer_wellness": {
                "name": "Summer Wellness Festival",
                "theme": "health_vitality",
                "duration_days": 90,
                "special_rewards": {
                    "wellness_warrior": {
                        "experience": 800,
                        "title": "Wellness Warrior",
                        "special_item": "Summer Sun Badge"
                    }
                },
                "special_quests": [
                    {
                        "title": "Hydration Hero",
                        "description": "Log water intake every day for 30 days",
                        "requirements": {"habit_category": "wellness", "daily_completions": 30}
                    }
                ]
            },
            "productivity_autumn": {
                "name": "Autumn Productivity Drive",
                "theme": "focus_achievement", 
                "duration_days": 60,
                "special_rewards": {
                    "productivity_master": {
                        "experience": 600,
                        "title": "Productivity Master",
                        "special_item": "Golden Leaf Badge"
                    }
                },
                "special_quests": [
                    {
                        "title": "Focus Mastery",
                        "description": "Complete productivity habits 100 times",
                        "requirements": {"habit_category": "productivity", "total_completions": 100}
                    }
                ]
            }
        }
    
    async def get_active_seasonal_events(self) -> List[SeasonalEvent]:
        """Get currently active seasonal events"""
        
        now = datetime.now()
        
        query = """
        SELECT * FROM seasonal_events
        WHERE start_date <= :now AND end_date > :now
        ORDER BY start_date
        """
        
        result = await self.db.execute(text(query), {"now": now})
        
        events = []
        for row in result:
            events.append(SeasonalEvent(
                id=row.id,
                name=row.name,
                theme=row.theme,
                description=row.description,
                start_date=row.start_date,
                end_date=row.end_date,
                special_quests=json.loads(row.special_quests or '[]'),
                special_rewards=json.loads(row.special_rewards or '{}'),
                participation_requirements=json.loads(row.participation_requirements or '{}'),
                leaderboard=json.loads(row.leaderboard or '{}')
            ))
        
        return events
    
    async def create_seasonal_event(self, event_data: Dict) -> SeasonalEvent:
        """Create a new seasonal event"""
        
        event_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO seasonal_events (id, name, theme, description, start_date, end_date,
                                   special_quests, special_rewards, participation_requirements)
        VALUES (:id, :name, :theme, :description, :start_date, :end_date,
                :special_quests, :special_rewards, :participation_requirements)
        """
        
        await self.db.execute(text(query), {
            "id": event_id,
            "name": event_data["name"],
            "theme": event_data["theme"],
            "description": event_data["description"],
            "start_date": event_data["start_date"],
            "end_date": event_data["end_date"],
            "special_quests": json.dumps(event_data.get("special_quests", [])),
            "special_rewards": json.dumps(event_data.get("special_rewards", {})),
            "participation_requirements": json.dumps(event_data.get("participation_requirements", {}))
        })
        
        return SeasonalEvent(
            id=event_id,
            name=event_data["name"],
            theme=event_data["theme"],
            description=event_data["description"],
            start_date=event_data["start_date"],
            end_date=event_data["end_date"],
            special_quests=event_data.get("special_quests", []),
            special_rewards=event_data.get("special_rewards", {}),
            participation_requirements=event_data.get("participation_requirements", {}),
            leaderboard={}
        )


# FastAPI endpoints for advanced gamification
async def get_daily_quests(user_id: int, db: Session) -> List[Dict]:
    """Get daily quests for a user"""
    
    generator = QuestGenerator(db)
    quests = await generator.generate_daily_quests(user_id)
    return [asdict(quest) for quest in quests]


async def get_user_guild(user_id: int, db: Session) -> Optional[Dict]:
    """Get user's guild information"""
    
    query = """
    SELECT g.*, gm.role, gm.joined_at
    FROM guilds g
    JOIN guild_members gm ON g.id = gm.guild_id
    WHERE gm.user_id = :user_id
    """
    
    result = await db.execute(text(query), {"user_id": user_id})
    row = result.first()
    
    if not row:
        return None
    
    guild_manager = GuildManager(db)
    guild = await guild_manager.get_guild(row.id)
    
    if guild:
        guild_dict = asdict(guild)
        guild_dict["user_role"] = row.role
        guild_dict["joined_at"] = row.joined_at
        return guild_dict
    
    return None


async def get_seasonal_events(db: Session) -> List[Dict]:
    """Get active seasonal events"""
    
    manager = SeasonalEventManager(db)
    events = await manager.get_active_seasonal_events()
    return [asdict(event) for event in events]