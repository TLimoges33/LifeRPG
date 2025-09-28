"""
Community Features System - Social Engagement and Habit Buddies
Enables users to connect, share progress, and motivate each other
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from fastapi import HTTPException

from .models import User, Habit, Log
from .db import get_db


class ChallengeStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChallengeType(Enum):
    INDIVIDUAL = "individual"  # Personal challenge
    GROUP = "group"           # Multiple participants
    COMMUNITY = "community"   # Open to all users


@dataclass
class Community:
    """Represents a community/group of users"""
    id: int
    name: str
    description: str
    category: str  # fitness, productivity, wellness, etc.
    is_public: bool
    member_count: int
    created_by: int
    created_at: datetime
    tags: List[str]
    rules: Dict[str, Any]


@dataclass
class HabitBuddy:
    """Represents a habit accountability partnership"""
    id: int
    user1_id: int
    user2_id: int
    shared_habits: List[int]  # habit IDs they're tracking together
    status: str  # active, paused, completed
    created_at: datetime
    motivation_message: str
    check_in_frequency: str  # daily, weekly


@dataclass
class Challenge:
    """Represents a habit challenge"""
    id: int
    title: str
    description: str
    challenge_type: ChallengeType
    status: ChallengeStatus
    start_date: datetime
    end_date: datetime
    creator_id: int
    participants: List[int]
    habit_template: Dict[str, Any]
    rewards: Dict[str, Any]
    rules: Dict[str, Any]
    progress: Dict[int, Any]  # user_id -> progress data


@dataclass
class Achievement:
    """Community achievement/badge"""
    id: int
    title: str
    description: str
    icon: str
    category: str
    requirements: Dict[str, Any]
    rarity: str  # common, rare, epic, legendary
    points: int


@dataclass
class SocialPost:
    """Social media style post about habits"""
    id: int
    user_id: int
    content: str
    post_type: str  # milestone, motivation, question, celebration
    habit_id: Optional[int]
    media_urls: List[str]
    likes: int
    comments: List[Dict]
    created_at: datetime
    visibility: str  # public, friends, private


class CommunityManager:
    """Manages community features and social interactions"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_community(self, creator_id: int, community_data: Dict) -> Community:
        """Create a new community"""
        
        # Validate community data
        required_fields = ['name', 'description', 'category']
        for field in required_fields:
            if field not in community_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Insert into database
        query = """
        INSERT INTO communities (name, description, category, is_public, 
                               created_by, created_at, tags, rules)
        VALUES (:name, :description, :category, :is_public, 
                :created_by, :created_at, :tags, :rules)
        RETURNING id
        """
        
        result = await self.db.execute(text(query), {
            'name': community_data['name'],
            'description': community_data['description'], 
            'category': community_data['category'],
            'is_public': community_data.get('is_public', True),
            'created_by': creator_id,
            'created_at': datetime.now(),
            'tags': json.dumps(community_data.get('tags', [])),
            'rules': json.dumps(community_data.get('rules', {}))
        })
        
        community_id = result.scalar()
        
        # Add creator as first member
        await self._add_community_member(community_id, creator_id, role='admin')
        
        # Return the created community
        return await self.get_community(community_id)
    
    async def get_community(self, community_id: int) -> Optional[Community]:
        """Get community details"""
        
        query = """
        SELECT c.*, COUNT(cm.user_id) as member_count
        FROM communities c
        LEFT JOIN community_members cm ON c.id = cm.community_id
        WHERE c.id = :community_id
        GROUP BY c.id
        """
        
        result = await self.db.execute(text(query), {'community_id': community_id})
        row = result.first()
        
        if not row:
            return None
        
        return Community(
            id=row.id,
            name=row.name,
            description=row.description,
            category=row.category,
            is_public=row.is_public,
            member_count=row.member_count or 0,
            created_by=row.created_by,
            created_at=row.created_at,
            tags=json.loads(row.tags or '[]'),
            rules=json.loads(row.rules or '{}')
        )
    
    async def join_community(self, community_id: int, user_id: int) -> bool:
        """Join a community"""
        
        # Check if community exists and is public or user is invited
        community = await self.get_community(community_id)
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if already a member
        existing_member = await self._is_community_member(community_id, user_id)
        if existing_member:
            return False  # Already a member
        
        # Add as member
        await self._add_community_member(community_id, user_id, role='member')
        return True
    
    async def _add_community_member(self, community_id: int, user_id: int, role: str = 'member'):
        """Add a member to a community"""
        
        query = """
        INSERT INTO community_members (community_id, user_id, role, joined_at)
        VALUES (:community_id, :user_id, :role, :joined_at)
        ON CONFLICT (community_id, user_id) DO NOTHING
        """
        
        await self.db.execute(text(query), {
            'community_id': community_id,
            'user_id': user_id,
            'role': role,
            'joined_at': datetime.now()
        })
    
    async def _is_community_member(self, community_id: int, user_id: int) -> bool:
        """Check if user is a community member"""
        
        query = """
        SELECT 1 FROM community_members 
        WHERE community_id = :community_id AND user_id = :user_id
        """
        
        result = await self.db.execute(text(query), {
            'community_id': community_id,
            'user_id': user_id
        })
        
        return result.first() is not None
    
    async def create_habit_buddy_partnership(self, user1_id: int, user2_id: int, 
                                           shared_habits: List[int]) -> HabitBuddy:
        """Create a habit buddy partnership"""
        
        # Validate that both users exist and habits belong to one of them
        # Implementation depends on your user validation logic
        
        query = """
        INSERT INTO habit_buddies (user1_id, user2_id, shared_habits, status, 
                                 created_at, check_in_frequency)
        VALUES (:user1_id, :user2_id, :shared_habits, :status, 
                :created_at, :check_in_frequency)
        RETURNING id
        """
        
        result = await self.db.execute(text(query), {
            'user1_id': user1_id,
            'user2_id': user2_id,
            'shared_habits': json.dumps(shared_habits),
            'status': 'active',
            'created_at': datetime.now(),
            'check_in_frequency': 'daily'
        })
        
        buddy_id = result.scalar()
        
        return HabitBuddy(
            id=buddy_id,
            user1_id=user1_id,
            user2_id=user2_id,
            shared_habits=shared_habits,
            status='active',
            created_at=datetime.now(),
            motivation_message='',
            check_in_frequency='daily'
        )
    
    async def get_user_habit_buddies(self, user_id: int) -> List[HabitBuddy]:
        """Get all habit buddies for a user"""
        
        query = """
        SELECT hb.*, u1.username as user1_name, u2.username as user2_name
        FROM habit_buddies hb
        JOIN users u1 ON hb.user1_id = u1.id
        JOIN users u2 ON hb.user2_id = u2.id
        WHERE (hb.user1_id = :user_id OR hb.user2_id = :user_id)
        AND hb.status = 'active'
        ORDER BY hb.created_at DESC
        """
        
        result = await self.db.execute(text(query), {'user_id': user_id})
        
        buddies = []
        for row in result:
            buddies.append(HabitBuddy(
                id=row.id,
                user1_id=row.user1_id,
                user2_id=row.user2_id,
                shared_habits=json.loads(row.shared_habits or '[]'),
                status=row.status,
                created_at=row.created_at,
                motivation_message=row.motivation_message or '',
                check_in_frequency=row.check_in_frequency or 'daily'
            ))
        
        return buddies


class ChallengeManager:
    """Manages habit challenges and competitions"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_challenge(self, creator_id: int, challenge_data: Dict) -> Challenge:
        """Create a new challenge"""
        
        # Validate challenge data
        required_fields = ['title', 'description', 'challenge_type', 'start_date', 'end_date']
        for field in required_fields:
            if field not in challenge_data:
                raise ValueError(f"Missing required field: {field}")
        
        query = """
        INSERT INTO challenges (title, description, challenge_type, status,
                              start_date, end_date, creator_id, created_at,
                              habit_template, rewards, rules)
        VALUES (:title, :description, :challenge_type, :status,
                :start_date, :end_date, :creator_id, :created_at,
                :habit_template, :rewards, :rules)
        RETURNING id
        """
        
        result = await self.db.execute(text(query), {
            'title': challenge_data['title'],
            'description': challenge_data['description'],
            'challenge_type': challenge_data['challenge_type'],
            'status': ChallengeStatus.DRAFT.value,
            'start_date': challenge_data['start_date'],
            'end_date': challenge_data['end_date'],
            'creator_id': creator_id,
            'created_at': datetime.now(),
            'habit_template': json.dumps(challenge_data.get('habit_template', {})),
            'rewards': json.dumps(challenge_data.get('rewards', {})),
            'rules': json.dumps(challenge_data.get('rules', {}))
        })
        
        challenge_id = result.scalar()
        
        # Auto-join creator to their own challenge
        await self.join_challenge(challenge_id, creator_id)
        
        return await self.get_challenge(challenge_id)
    
    async def get_challenge(self, challenge_id: int) -> Optional[Challenge]:
        """Get challenge details"""
        
        query = """
        SELECT c.*, 
               COALESCE(
                   json_agg(
                       json_build_object('user_id', cp.user_id, 'joined_at', cp.joined_at)
                   ) FILTER (WHERE cp.user_id IS NOT NULL), 
                   '[]'
               ) as participants_data
        FROM challenges c
        LEFT JOIN challenge_participants cp ON c.id = cp.challenge_id
        WHERE c.id = :challenge_id
        GROUP BY c.id
        """
        
        result = await self.db.execute(text(query), {'challenge_id': challenge_id})
        row = result.first()
        
        if not row:
            return None
        
        participants_data = json.loads(row.participants_data)
        participants = [p['user_id'] for p in participants_data]
        
        return Challenge(
            id=row.id,
            title=row.title,
            description=row.description,
            challenge_type=ChallengeType(row.challenge_type),
            status=ChallengeStatus(row.status),
            start_date=row.start_date,
            end_date=row.end_date,
            creator_id=row.creator_id,
            participants=participants,
            habit_template=json.loads(row.habit_template or '{}'),
            rewards=json.loads(row.rewards or '{}'),
            rules=json.loads(row.rules or '{}'),
            progress={}  # Will be populated separately if needed
        )
    
    async def join_challenge(self, challenge_id: int, user_id: int) -> bool:
        """Join a challenge"""
        
        # Check if challenge exists and is joinable
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        if challenge.status not in [ChallengeStatus.DRAFT, ChallengeStatus.ACTIVE]:
            raise HTTPException(status_code=400, detail="Challenge not joinable")
        
        # Check if already participating
        if user_id in challenge.participants:
            return False  # Already participating
        
        # Add participant
        query = """
        INSERT INTO challenge_participants (challenge_id, user_id, joined_at)
        VALUES (:challenge_id, :user_id, :joined_at)
        ON CONFLICT (challenge_id, user_id) DO NOTHING
        """
        
        await self.db.execute(text(query), {
            'challenge_id': challenge_id,
            'user_id': user_id,
            'joined_at': datetime.now()
        })
        
        return True
    
    async def get_active_challenges(self, user_id: Optional[int] = None, 
                                  limit: int = 20) -> List[Challenge]:
        """Get active challenges, optionally filtered by user participation"""
        
        base_query = """
        SELECT c.*, 
               COUNT(cp.user_id) as participant_count,
               CASE WHEN :user_id IS NULL THEN FALSE 
                    ELSE EXISTS(
                        SELECT 1 FROM challenge_participants cp2 
                        WHERE cp2.challenge_id = c.id AND cp2.user_id = :user_id
                    ) END as user_participating
        FROM challenges c
        LEFT JOIN challenge_participants cp ON c.id = cp.challenge_id
        WHERE c.status = 'active'
        AND c.start_date <= :now
        AND c.end_date > :now
        """
        
        if user_id:
            base_query += """
            AND (c.challenge_type = 'community' 
                 OR EXISTS(
                     SELECT 1 FROM challenge_participants cp3 
                     WHERE cp3.challenge_id = c.id AND cp3.user_id = :user_id
                 ))
            """
        
        base_query += """
        GROUP BY c.id
        ORDER BY c.start_date DESC
        LIMIT :limit
        """
        
        result = await self.db.execute(text(base_query), {
            'user_id': user_id,
            'now': datetime.now(),
            'limit': limit
        })
        
        challenges = []
        for row in result:
            # Get participants for this challenge
            participants = await self._get_challenge_participants(row.id)
            
            challenges.append(Challenge(
                id=row.id,
                title=row.title,
                description=row.description,
                challenge_type=ChallengeType(row.challenge_type),
                status=ChallengeStatus(row.status),
                start_date=row.start_date,
                end_date=row.end_date,
                creator_id=row.creator_id,
                participants=participants,
                habit_template=json.loads(row.habit_template or '{}'),
                rewards=json.loads(row.rewards or '{}'),
                rules=json.loads(row.rules or '{}'),
                progress={}
            ))
        
        return challenges
    
    async def _get_challenge_participants(self, challenge_id: int) -> List[int]:
        """Get list of participant user IDs for a challenge"""
        
        query = """
        SELECT user_id FROM challenge_participants 
        WHERE challenge_id = :challenge_id
        """
        
        result = await self.db.execute(text(query), {'challenge_id': challenge_id})
        return [row.user_id for row in result]
    
    async def update_challenge_progress(self, challenge_id: int, user_id: int, 
                                      progress_data: Dict):
        """Update a user's progress in a challenge"""
        
        query = """
        INSERT INTO challenge_progress (challenge_id, user_id, progress_data, updated_at)
        VALUES (:challenge_id, :user_id, :progress_data, :updated_at)
        ON CONFLICT (challenge_id, user_id) 
        DO UPDATE SET 
            progress_data = :progress_data,
            updated_at = :updated_at
        """
        
        await self.db.execute(text(query), {
            'challenge_id': challenge_id,
            'user_id': user_id,
            'progress_data': json.dumps(progress_data),
            'updated_at': datetime.now()
        })
    
    async def get_challenge_leaderboard(self, challenge_id: int) -> List[Dict]:
        """Get leaderboard for a challenge"""
        
        query = """
        SELECT 
            cp.user_id,
            u.username,
            cp.progress_data,
            cp.updated_at,
            ROW_NUMBER() OVER (ORDER BY 
                CAST(cp.progress_data->>'score' AS INTEGER) DESC,
                cp.updated_at ASC
            ) as rank
        FROM challenge_progress cp
        JOIN users u ON cp.user_id = u.id
        WHERE cp.challenge_id = :challenge_id
        ORDER BY rank
        LIMIT 50
        """
        
        result = await self.db.execute(text(query), {'challenge_id': challenge_id})
        
        leaderboard = []
        for row in result:
            leaderboard.append({
                'rank': row.rank,
                'user_id': row.user_id,
                'username': row.username,
                'progress': json.loads(row.progress_data or '{}'),
                'last_updated': row.updated_at
            })
        
        return leaderboard


class SocialFeedManager:
    """Manages social feed and posts"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_post(self, user_id: int, post_data: Dict) -> SocialPost:
        """Create a social post"""
        
        query = """
        INSERT INTO social_posts (user_id, content, post_type, habit_id,
                                media_urls, created_at, visibility)
        VALUES (:user_id, :content, :post_type, :habit_id,
                :media_urls, :created_at, :visibility)
        RETURNING id
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'content': post_data['content'],
            'post_type': post_data.get('post_type', 'general'),
            'habit_id': post_data.get('habit_id'),
            'media_urls': json.dumps(post_data.get('media_urls', [])),
            'created_at': datetime.now(),
            'visibility': post_data.get('visibility', 'public')
        })
        
        post_id = result.scalar()
        
        return SocialPost(
            id=post_id,
            user_id=user_id,
            content=post_data['content'],
            post_type=post_data.get('post_type', 'general'),
            habit_id=post_data.get('habit_id'),
            media_urls=post_data.get('media_urls', []),
            likes=0,
            comments=[],
            created_at=datetime.now(),
            visibility=post_data.get('visibility', 'public')
        )
    
    async def get_user_feed(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get social feed for a user"""
        
        query = """
        SELECT 
            sp.*,
            u.username,
            u.avatar_url,
            COUNT(spl.id) as likes_count,
            COUNT(spc.id) as comments_count
        FROM social_posts sp
        JOIN users u ON sp.user_id = u.id
        LEFT JOIN social_post_likes spl ON sp.id = spl.post_id
        LEFT JOIN social_post_comments spc ON sp.id = spc.post_id
        WHERE sp.visibility = 'public'
        OR sp.user_id = :user_id
        OR sp.user_id IN (
            SELECT user2_id FROM habit_buddies WHERE user1_id = :user_id
            UNION
            SELECT user1_id FROM habit_buddies WHERE user2_id = :user_id
        )
        GROUP BY sp.id, u.username, u.avatar_url
        ORDER BY sp.created_at DESC
        LIMIT :limit
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'limit': limit
        })
        
        feed = []
        for row in result:
            feed.append({
                'id': row.id,
                'user_id': row.user_id,
                'username': row.username,
                'avatar_url': row.avatar_url,
                'content': row.content,
                'post_type': row.post_type,
                'habit_id': row.habit_id,
                'media_urls': json.loads(row.media_urls or '[]'),
                'likes': row.likes_count,
                'comments': row.comments_count,
                'created_at': row.created_at,
                'visibility': row.visibility
            })
        
        return feed
    
    async def like_post(self, post_id: int, user_id: int) -> bool:
        """Like or unlike a post"""
        
        # Check if already liked
        query = """
        SELECT 1 FROM social_post_likes 
        WHERE post_id = :post_id AND user_id = :user_id
        """
        
        result = await self.db.execute(text(query), {
            'post_id': post_id,
            'user_id': user_id
        })
        
        if result.first():
            # Unlike
            delete_query = """
            DELETE FROM social_post_likes 
            WHERE post_id = :post_id AND user_id = :user_id
            """
            await self.db.execute(text(delete_query), {
                'post_id': post_id,
                'user_id': user_id
            })
            return False
        else:
            # Like
            insert_query = """
            INSERT INTO social_post_likes (post_id, user_id, created_at)
            VALUES (:post_id, :user_id, :created_at)
            """
            await self.db.execute(text(insert_query), {
                'post_id': post_id,
                'user_id': user_id,
                'created_at': datetime.now()
            })
            return True


# FastAPI endpoints for community features
async def create_community_endpoint(creator_id: int, community_data: Dict, 
                                  db: Session) -> Dict:
    """Create a new community"""
    
    manager = CommunityManager(db)
    community = await manager.create_community(creator_id, community_data)
    return asdict(community)


async def get_user_communities(user_id: int, db: Session) -> List[Dict]:
    """Get communities for a user"""
    
    query = """
    SELECT c.*, cm.role, cm.joined_at
    FROM communities c
    JOIN community_members cm ON c.id = cm.community_id
    WHERE cm.user_id = :user_id
    ORDER BY cm.joined_at DESC
    """
    
    result = await db.execute(text(query), {'user_id': user_id})
    
    communities = []
    for row in result:
        communities.append({
            'id': row.id,
            'name': row.name,
            'description': row.description,
            'category': row.category,
            'is_public': row.is_public,
            'created_by': row.created_by,
            'created_at': row.created_at,
            'tags': json.loads(row.tags or '[]'),
            'user_role': row.role,
            'joined_at': row.joined_at
        })
    
    return communities