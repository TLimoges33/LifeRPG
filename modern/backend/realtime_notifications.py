"""
Real-time Notifications System with WebSocket Support
Provides instant notifications for habit reminders, achievements, and social interactions
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from .models import User, Habit, Log
from .db import get_db

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    HABIT_REMINDER = "habit_reminder"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    QUEST_COMPLETED = "quest_completed"
    STREAK_MILESTONE = "streak_milestone"
    GUILD_INVITATION = "guild_invitation"
    BUDDY_ENCOURAGEMENT = "buddy_encouragement"
    CHALLENGE_UPDATE = "challenge_update"
    SOCIAL_INTERACTION = "social_interaction"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Notification:
    """Represents a notification to be sent to a user"""
    id: str
    user_id: int
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    priority: NotificationPriority
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    action_url: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class HabitReminder:
    """Habit reminder configuration"""
    habit_id: int
    user_id: int
    reminder_time: str  # HH:MM format
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    is_active: bool
    message_template: str
    advance_minutes: int = 0  # Remind X minutes before


class WebSocketManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, 
                     device_info: Optional[Dict] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "device_info": device_info or {},
            "last_ping": datetime.now()
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send connection confirmation
        await self.send_to_user(user_id, {
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "message": "Real-time notifications are now active!"
        })
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.connection_metadata:
            user_id = self.connection_metadata[websocket]["user_id"]
            
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Remove user entry if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: int, data: Dict):
        """Send data to all connections for a specific user"""
        if user_id in self.active_connections:
            disconnected_connections = set()
            
            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(json.dumps(data))
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    disconnected_connections.add(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected_connections:
                self.disconnect(websocket)
    
    async def send_to_all(self, data: Dict):
        """Send data to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, data)
    
    async def ping_connections(self):
        """Send ping to maintain connections"""
        ping_data = {"type": "ping", "timestamp": datetime.now().isoformat()}
        
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, ping_data)
    
    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, set()))


class NotificationManager:
    """Manages notification creation, scheduling, and delivery"""
    
    def __init__(self, db_session: Session, websocket_manager: WebSocketManager):
        self.db = db_session
        self.ws_manager = websocket_manager
        self.scheduled_notifications: List[Notification] = []
    
    async def create_notification(self, notification: Notification) -> str:
        """Create and optionally schedule a notification"""
        
        # Save to database
        query = """
        INSERT INTO notifications (id, user_id, type, title, message, data,
                                 priority, created_at, scheduled_for, action_url, image_url)
        VALUES (:id, :user_id, :type, :title, :message, :data,
                :priority, :created_at, :scheduled_for, :action_url, :image_url)
        """
        
        await self.db.execute(text(query), {
            "id": notification.id,
            "user_id": notification.user_id,
            "type": notification.type.value,
            "title": notification.title,
            "message": notification.message,
            "data": json.dumps(notification.data),
            "priority": notification.priority.value,
            "created_at": notification.created_at,
            "scheduled_for": notification.scheduled_for,
            "action_url": notification.action_url,
            "image_url": notification.image_url
        })
        
        # Send immediately if not scheduled
        if notification.scheduled_for is None:
            await self._send_notification(notification)
        else:
            self.scheduled_notifications.append(notification)
        
        return notification.id
    
    async def _send_notification(self, notification: Notification):
        """Send notification via WebSocket and mark as sent"""
        
        notification_data = {
            "type": "notification",
            "notification": {
                "id": notification.id,
                "type": notification.type.value,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority.value,
                "created_at": notification.created_at.isoformat(),
                "action_url": notification.action_url,
                "image_url": notification.image_url,
                "data": notification.data
            }
        }
        
        await self.ws_manager.send_to_user(notification.user_id, notification_data)
        
        # Log notification sent
        logger.info(f"Notification sent: {notification.id} to user {notification.user_id}")
    
    async def send_habit_reminder(self, habit_id: int, user_id: int, custom_message: Optional[str] = None):
        """Send a habit reminder notification"""
        
        # Get habit details
        query = """
        SELECT title, description FROM habits WHERE id = :habit_id AND user_id = :user_id
        """
        result = await self.db.execute(text(query), {"habit_id": habit_id, "user_id": user_id})
        habit = result.first()
        
        if not habit:
            return
        
        message = custom_message or f"Time to work on your {habit.title} habit!"
        
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.HABIT_REMINDER,
            title="🔔 Habit Reminder",
            message=message,
            data={
                "habit_id": habit_id,
                "habit_title": habit.title,
                "habit_description": habit.description
            },
            priority=NotificationPriority.MEDIUM,
            created_at=datetime.now(),
            action_url=f"/habits/{habit_id}"
        )
        
        await self.create_notification(notification)
    
    async def send_achievement_notification(self, user_id: int, achievement_data: Dict):
        """Send achievement unlocked notification"""
        
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.ACHIEVEMENT_UNLOCKED,
            title="🏆 Achievement Unlocked!",
            message=f"Congratulations! You've earned: {achievement_data['title']}",
            data=achievement_data,
            priority=NotificationPriority.HIGH,
            created_at=datetime.now(),
            action_url="/achievements",
            image_url=achievement_data.get("icon_url")
        )
        
        await self.create_notification(notification)
    
    async def send_streak_milestone(self, user_id: int, habit_id: int, streak_count: int):
        """Send streak milestone notification"""
        
        # Get habit title
        query = "SELECT title FROM habits WHERE id = :habit_id"
        result = await self.db.execute(text(query), {"habit_id": habit_id})
        habit = result.first()
        
        if not habit:
            return
        
        milestone_messages = {
            7: "Amazing! One week strong! 🔥",
            14: "Two weeks of consistency! You're on fire! 🌟",
            30: "30-day streak! You're a habit hero! 🦸‍♀️",
            50: "50 days! Nothing can stop you now! 💪",
            100: "100-day milestone! You're absolutely legendary! 👑"
        }
        
        message = milestone_messages.get(streak_count, f"{streak_count}-day streak! Keep it up!")
        
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.STREAK_MILESTONE,
            title="🔥 Streak Milestone!",
            message=f"{habit.title}: {message}",
            data={
                "habit_id": habit_id,
                "habit_title": habit.title,
                "streak_count": streak_count
            },
            priority=NotificationPriority.HIGH,
            created_at=datetime.now(),
            action_url=f"/habits/{habit_id}"
        )
        
        await self.create_notification(notification)
    
    async def send_social_notification(self, user_id: int, notification_data: Dict):
        """Send social interaction notification"""
        
        notification_types = {
            "like": "liked your post",
            "comment": "commented on your post", 
            "follow": "started following you",
            "buddy_request": "sent you a habit buddy request",
            "guild_invite": "invited you to join their guild"
        }
        
        action_type = notification_data["action_type"]
        from_user = notification_data["from_user"]
        
        message = f"{from_user} {notification_types.get(action_type, 'interacted with you')}"
        
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.SOCIAL_INTERACTION,
            title="👥 Social Update",
            message=message,
            data=notification_data,
            priority=NotificationPriority.MEDIUM,
            created_at=datetime.now(),
            action_url=notification_data.get("action_url", "/social")
        )
        
        await self.create_notification(notification)
    
    async def process_scheduled_notifications(self):
        """Process and send scheduled notifications"""
        
        now = datetime.now()
        notifications_to_send = []
        
        for notification in self.scheduled_notifications[:]:
            if notification.scheduled_for and notification.scheduled_for <= now:
                notifications_to_send.append(notification)
                self.scheduled_notifications.remove(notification)
        
        for notification in notifications_to_send:
            await self._send_notification(notification)
    
    async def get_user_notifications(self, user_id: int, limit: int = 50, 
                                   unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        
        query = """
        SELECT * FROM notifications 
        WHERE user_id = :user_id
        """
        
        if unread_only:
            query += " AND read_at IS NULL"
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        result = await self.db.execute(text(query), {
            "user_id": user_id,
            "limit": limit
        })
        
        notifications = []
        for row in result:
            notifications.append({
                "id": row.id,
                "type": row.type,
                "title": row.title,
                "message": row.message,
                "data": json.loads(row.data or '{}'),
                "priority": row.priority,
                "created_at": row.created_at,
                "read_at": row.read_at,
                "action_url": row.action_url,
                "image_url": row.image_url
            })
        
        return notifications
    
    async def mark_notification_read(self, notification_id: str, user_id: int):
        """Mark a notification as read"""
        
        query = """
        UPDATE notifications 
        SET read_at = :read_at
        WHERE id = :notification_id AND user_id = :user_id
        """
        
        await self.db.execute(text(query), {
            "notification_id": notification_id,
            "user_id": user_id,
            "read_at": datetime.now()
        })
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        
        query = """
        SELECT COUNT(*) as unread_count
        FROM notifications 
        WHERE user_id = :user_id AND read_at IS NULL
        """
        
        result = await self.db.execute(text(query), {"user_id": user_id})
        row = result.first()
        
        return row.unread_count if row else 0


class HabitReminderService:
    """Manages habit reminders and scheduling"""
    
    def __init__(self, db_session: Session, notification_manager: NotificationManager):
        self.db = db_session
        self.notification_manager = notification_manager
    
    async def create_habit_reminder(self, reminder_data: Dict) -> str:
        """Create a new habit reminder"""
        
        reminder_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO habit_reminders (id, habit_id, user_id, reminder_time,
                                   days_of_week, is_active, message_template, advance_minutes)
        VALUES (:id, :habit_id, :user_id, :reminder_time,
                :days_of_week, :is_active, :message_template, :advance_minutes)
        """
        
        await self.db.execute(text(query), {
            "id": reminder_id,
            "habit_id": reminder_data["habit_id"],
            "user_id": reminder_data["user_id"],
            "reminder_time": reminder_data["reminder_time"],
            "days_of_week": json.dumps(reminder_data.get("days_of_week", [0, 1, 2, 3, 4, 5, 6])),
            "is_active": reminder_data.get("is_active", True),
            "message_template": reminder_data.get("message_template", ""),
            "advance_minutes": reminder_data.get("advance_minutes", 0)
        })
        
        return reminder_id
    
    async def get_due_reminders(self) -> List[HabitReminder]:
        """Get habit reminders that are due to be sent"""
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_weekday = now.weekday()
        
        query = """
        SELECT hr.*, h.title as habit_title
        FROM habit_reminders hr
        JOIN habits h ON hr.habit_id = h.id
        WHERE hr.is_active = true
        AND hr.reminder_time = :current_time
        AND JSON_EXTRACT(hr.days_of_week, '$[*]') LIKE :weekday_pattern
        """
        
        # SQLite JSON query to check if current weekday is in the array
        weekday_pattern = f'%{current_weekday}%'
        
        result = await self.db.execute(text(query), {
            "current_time": current_time,
            "weekday_pattern": weekday_pattern
        })
        
        reminders = []
        for row in result:
            days_of_week = json.loads(row.days_of_week or '[]')
            if current_weekday in days_of_week:
                reminders.append(HabitReminder(
                    habit_id=row.habit_id,
                    user_id=row.user_id,
                    reminder_time=row.reminder_time,
                    days_of_week=days_of_week,
                    is_active=row.is_active,
                    message_template=row.message_template or f"Time for your {row.habit_title} habit!",
                    advance_minutes=row.advance_minutes or 0
                ))
        
        return reminders
    
    async def send_due_reminders(self):
        """Send all due habit reminders"""
        
        reminders = await self.get_due_reminders()
        
        for reminder in reminders:
            await self.notification_manager.send_habit_reminder(
                habit_id=reminder.habit_id,
                user_id=reminder.user_id,
                custom_message=reminder.message_template
            )


# Global instances
websocket_manager = WebSocketManager()
notification_manager = None  # Initialized with database session


async def notification_scheduler():
    """Background task to process scheduled notifications and reminders"""
    
    while True:
        try:
            if notification_manager:
                # Process scheduled notifications
                await notification_manager.process_scheduled_notifications()
                
                # Process habit reminders
                reminder_service = HabitReminderService(notification_manager.db, notification_manager)
                await reminder_service.send_due_reminders()
                
                # Ping WebSocket connections
                await websocket_manager.ping_connections()
            
            # Wait 60 seconds before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}")
            await asyncio.sleep(60)


# FastAPI WebSocket endpoint
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications"""
    
    try:
        await websocket_manager.connect(websocket, user_id)
        
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "mark_read":
                    if notification_manager:
                        await notification_manager.mark_notification_read(
                            message["notification_id"], user_id
                        )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        websocket_manager.disconnect(websocket)


# FastAPI endpoints for notifications
async def get_notifications(user_id: int, unread_only: bool = False, 
                          limit: int = 50, db: Session = None) -> Dict:
    """Get user notifications"""
    
    if not notification_manager:
        return {"notifications": [], "unread_count": 0}
    
    notifications = await notification_manager.get_user_notifications(
        user_id, limit, unread_only
    )
    unread_count = await notification_manager.get_unread_count(user_id)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "has_more": len(notifications) == limit
    }


async def mark_notification_read(notification_id: str, user_id: int, db: Session = None):
    """Mark notification as read"""
    
    if notification_manager:
        await notification_manager.mark_notification_read(notification_id, user_id)
    
    return {"success": True}


async def create_habit_reminder(user_id: int, reminder_data: Dict, db: Session = None) -> Dict:
    """Create a habit reminder"""
    
    if not notification_manager:
        return {"error": "Notification system not available"}
    
    reminder_service = HabitReminderService(db, notification_manager)
    reminder_id = await reminder_service.create_habit_reminder({
        **reminder_data,
        "user_id": user_id
    })
    
    return {"reminder_id": reminder_id, "success": True}