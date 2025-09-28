"""
Advanced Analytics Service - Comprehensive data analysis and insights
Provides deep analytics, pattern detection, and performance metrics
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import calendar
from collections import defaultdict, Counter

from .models import User, Habit, Log
from .ai_insights import AIRecommendationEngine


@dataclass
class AnalyticsKPIs:
    """Key Performance Indicators for analytics dashboard"""
    overall_completion_rate: float
    completion_rate_change: float
    active_streaks: int
    streak_change: float
    total_achievements: int
    achievement_change: float
    active_categories: int
    category_change: float
    total_habits: int
    habits_change: float


@dataclass
class CategoryAnalysis:
    """Analysis of habit categories"""
    category: str
    habit_count: int
    completion_rate: float
    average_streak: float
    total_completions: int
    difficulty_distribution: Dict[int, int]


@dataclass
class StreakAnalysis:
    """Streak performance analysis"""
    habit_id: int
    habit_title: str
    current_streak: int
    best_streak: int
    average_streak: float
    streak_consistency: float  # 0-1, how often streaks are maintained
    total_attempts: int


@dataclass
class TimeAnalysis:
    """Time-based performance analysis"""
    hour: int
    day_of_week: int
    completions: int
    success_rate: float
    habits_active: int


class AdvancedAnalyticsService:
    """Comprehensive analytics service for habit tracking data"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def get_comprehensive_analytics(self, user_id: int, 
                                        time_range: str = '30d',
                                        metrics: List[str] = None) -> Dict[str, Any]:
        """Get comprehensive analytics data for dashboard"""
        
        start_date, end_date = self._parse_time_range(time_range)
        
        analytics_data = {
            'time_range': time_range,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'generated_at': datetime.now().isoformat()
        }
        
        # Get KPIs
        analytics_data['kpis'] = await self._calculate_kpis(user_id, start_date, end_date)
        
        # Get completion trend
        analytics_data['completion_trend'] = await self._get_completion_trend(
            user_id, start_date, end_date
        )
        
        # Get category distribution
        analytics_data['category_distribution'] = await self._get_category_distribution(
            user_id, start_date, end_date
        )
        
        # Get weekly heatmap
        analytics_data['weekly_heatmap'] = await self._generate_weekly_heatmap(
            user_id, start_date, end_date
        )
        
        # Get difficulty analysis
        analytics_data['difficulty_analysis'] = await self._analyze_difficulty_performance(
            user_id, start_date, end_date
        )
        
        # Get hourly performance
        analytics_data['hourly_performance'] = await self._analyze_hourly_performance(
            user_id, start_date, end_date
        )
        
        # Get streak analysis
        analytics_data['streak_analysis'] = await self._analyze_streaks(
            user_id, start_date, end_date
        )
        
        # Get AI insights
        ai_engine = AIRecommendationEngine(self.db)
        insights = await ai_engine.generate_insights(user_id)
        analytics_data['ai_insights'] = [
            {
                'title': insight.title,
                'description': insight.description,
                'recommendations': insight.actionable_suggestions,
                'confidence': insight.priority_score
            }
            for insight in insights[:6]  # Top 6 insights
        ]
        
        return analytics_data
    
    def _parse_time_range(self, time_range: str) -> Tuple[datetime, datetime]:
        """Parse time range string into start and end dates"""
        
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        
        if time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        elif time_range == '1y':
            start_date = end_date - timedelta(days=365)
        elif time_range == 'all':
            start_date = datetime(2020, 1, 1)  # Far back date
        else:
            start_date = end_date - timedelta(days=30)  # Default to 30 days
        
        return start_date, end_date
    
    async def _calculate_kpis(self, user_id: int, start_date: datetime, 
                            end_date: datetime) -> AnalyticsKPIs:
        """Calculate key performance indicators"""
        
        # Current period query
        current_query = """
        SELECT 
            COUNT(DISTINCT h.id) as total_habits,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions,
            COUNT(l.id) as total_logs,
            COUNT(DISTINCT h.category) as active_categories
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id 
            AND l.timestamp BETWEEN :start_date AND :end_date
        WHERE h.user_id = :user_id
        AND h.created_at <= :end_date
        """
        
        result = await self.db.execute(text(current_query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        })
        current = result.first()
        
        # Previous period for comparison
        period_length = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_length)
        prev_end = start_date
        
        prev_result = await self.db.execute(text(current_query), {
            'user_id': user_id,
            'start_date': prev_start,
            'end_date': prev_end
        })
        previous = prev_result.first()
        
        # Calculate rates and changes
        current_completion_rate = (
            (current.completions / max(current.total_logs, 1)) * 100
            if current.total_logs else 0
        )
        
        prev_completion_rate = (
            (previous.completions / max(previous.total_logs, 1)) * 100
            if previous.total_logs else 0
        )
        
        completion_rate_change = (
            current_completion_rate - prev_completion_rate
            if prev_completion_rate else 0
        )
        
        # Get active streaks
        streaks_query = """
        SELECT COUNT(*) as active_streaks
        FROM (
            SELECT h.id, COUNT(*) as streak_length
            FROM habits h
            JOIN logs l ON h.id = l.habit_id
            WHERE h.user_id = :user_id
            AND l.action = 'completed'
            AND l.timestamp >= :recent_date
            GROUP BY h.id
            HAVING COUNT(*) >= 2
        ) streaks
        """
        
        recent_date = end_date - timedelta(days=7)
        streak_result = await self.db.execute(text(streaks_query), {
            'user_id': user_id,
            'recent_date': recent_date
        })
        active_streaks = streak_result.scalar() or 0
        
        # Get achievements (placeholder - implement based on your achievement system)
        achievements_query = """
        SELECT COUNT(*) as total_achievements
        FROM user_achievements ua
        WHERE ua.user_id = :user_id
        AND ua.unlocked_at BETWEEN :start_date AND :end_date
        """
        
        try:
            ach_result = await self.db.execute(text(achievements_query), {
                'user_id': user_id,
                'start_date': start_date,
                'end_date': end_date
            })
            total_achievements = ach_result.scalar() or 0
        except:
            total_achievements = 0
        
        return AnalyticsKPIs(
            overall_completion_rate=current_completion_rate,
            completion_rate_change=round(completion_rate_change, 1),
            active_streaks=active_streaks,
            streak_change=0.0,  # Implement streak change calculation
            total_achievements=total_achievements,
            achievement_change=0.0,  # Implement achievement change calculation
            active_categories=current.active_categories or 0,
            category_change=0.0,  # Implement category change calculation
            total_habits=current.total_habits or 0,
            habits_change=0.0  # Implement habits change calculation
        )
    
    async def _get_completion_trend(self, user_id: int, start_date: datetime, 
                                  end_date: datetime) -> List[Dict]:
        """Get daily completion rate trend"""
        
        query = """
        WITH date_range AS (
            SELECT date(datetime(:start_date, '+' || (value) || ' day')) as date
            FROM generate_series(0, :days - 1)
        ),
        daily_stats AS (
            SELECT 
                DATE(l.timestamp) as date,
                COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions,
                COUNT(l.id) as total_attempts
            FROM logs l
            JOIN habits h ON l.habit_id = h.id
            WHERE h.user_id = :user_id
            AND l.timestamp BETWEEN :start_date AND :end_date
            GROUP BY DATE(l.timestamp)
        )
        SELECT 
            dr.date,
            COALESCE(ds.completions, 0) as completions,
            COALESCE(ds.total_attempts, 0) as total_attempts,
            CASE 
                WHEN ds.total_attempts > 0 
                THEN (ds.completions * 100.0 / ds.total_attempts)
                ELSE 0 
            END as completion_rate,
            75.0 as target_rate
        FROM date_range dr
        LEFT JOIN daily_stats ds ON dr.date = ds.date
        ORDER BY dr.date
        """
        
        days = (end_date - start_date).days + 1
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date,
            'days': days
        })
        
        trend_data = []
        for row in result:
            trend_data.append({
                'date': row.date,
                'completion_rate': round(row.completion_rate, 1),
                'target_rate': row.target_rate,
                'completions': row.completions,
                'total_attempts': row.total_attempts
            })
        
        return trend_data
    
    async def _get_category_distribution(self, user_id: int, start_date: datetime,
                                       end_date: datetime) -> List[Dict]:
        """Get distribution of habits by category"""
        
        query = """
        SELECT 
            COALESCE(h.category, 'Uncategorized') as name,
            COUNT(h.id) as count,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id 
            AND l.timestamp BETWEEN :start_date AND :end_date
        WHERE h.user_id = :user_id
        GROUP BY h.category
        ORDER BY count DESC
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        distribution = []
        for row in result:
            distribution.append({
                'name': row.name,
                'count': row.count,
                'completions': row.completions
            })
        
        return distribution
    
    async def _generate_weekly_heatmap(self, user_id: int, start_date: datetime,
                                     end_date: datetime) -> List[List[Dict]]:
        """Generate a GitHub-style weekly heatmap of activity"""
        
        query = """
        SELECT 
            DATE(l.timestamp) as date,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions
        FROM logs l
        JOIN habits h ON l.habit_id = h.id
        WHERE h.user_id = :user_id
        AND l.timestamp BETWEEN :start_date AND :end_date
        GROUP BY DATE(l.timestamp)
        ORDER BY date
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Convert to dictionary for quick lookup
        daily_completions = {row.date: row.completions for row in result}
        
        # Generate heatmap data
        heatmap = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        # Start from Monday of the first week
        days_back = current_date.weekday()
        week_start = current_date - timedelta(days=days_back)
        
        max_completions = max(daily_completions.values()) if daily_completions else 1
        
        while week_start <= end_date_only:
            week = []
            for i in range(7):  # 7 days in a week
                day = week_start + timedelta(days=i)
                completions = daily_completions.get(day, 0)
                
                week.append({
                    'date': day.isoformat(),
                    'completions': completions,
                    'intensity': min(completions / max_completions, 1.0) if max_completions else 0
                })
            
            heatmap.append(week)
            week_start += timedelta(days=7)
        
        return heatmap
    
    async def _analyze_difficulty_performance(self, user_id: int, start_date: datetime,
                                            end_date: datetime) -> List[Dict]:
        """Analyze performance by habit difficulty"""
        
        query = """
        SELECT 
            h.difficulty,
            COUNT(h.id) as habit_count,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions,
            COUNT(l.id) as total_attempts,
            CASE 
                WHEN COUNT(l.id) > 0 
                THEN (COUNT(CASE WHEN l.action = 'completed' THEN 1 END) * 100.0 / COUNT(l.id))
                ELSE 0 
            END as success_rate
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id 
            AND l.timestamp BETWEEN :start_date AND :end_date
        WHERE h.user_id = :user_id
        AND h.difficulty IS NOT NULL
        GROUP BY h.difficulty
        ORDER BY h.difficulty
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        difficulty_data = []
        for row in result:
            difficulty_data.append({
                'difficulty': f"Level {row.difficulty}",
                'habit_count': row.habit_count,
                'success_rate': round(row.success_rate, 1),
                'completions': row.completions,
                'total_attempts': row.total_attempts
            })
        
        return difficulty_data
    
    async def _analyze_hourly_performance(self, user_id: int, start_date: datetime,
                                        end_date: datetime) -> List[Dict]:
        """Analyze performance by hour of day"""
        
        query = """
        SELECT 
            CAST(strftime('%H', l.timestamp) AS INTEGER) as hour,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions,
            COUNT(l.id) as total_attempts
        FROM logs l
        JOIN habits h ON l.habit_id = h.id
        WHERE h.user_id = :user_id
        AND l.timestamp BETWEEN :start_date AND :end_date
        GROUP BY hour
        ORDER BY hour
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        hourly_data = []
        for row in result:
            hourly_data.append({
                'hour': row.hour,
                'completions': row.completions,
                'total_attempts': row.total_attempts,
                'success_rate': (row.completions / max(row.total_attempts, 1)) * 100
            })
        
        return hourly_data
    
    async def _analyze_streaks(self, user_id: int, start_date: datetime,
                             end_date: datetime) -> List[Dict]:
        """Analyze streak performance for each habit"""
        
        query = """
        SELECT 
            h.id,
            h.title,
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as total_completions
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id 
            AND l.timestamp BETWEEN :start_date AND :end_date
        WHERE h.user_id = :user_id
        GROUP BY h.id, h.title
        HAVING total_completions > 0
        ORDER BY total_completions DESC
        LIMIT 10
        """
        
        result = await self.db.execute(text(query), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        streak_data = []
        for row in result:
            # Calculate current streak for this habit
            current_streak = await self._calculate_current_streak(row.id)
            best_streak = await self._calculate_best_streak(row.id)
            
            streak_data.append({
                'habit_id': row.id,
                'title': row.title,
                'current_streak': current_streak,
                'best_streak': best_streak,
                'average_streak': round((current_streak + best_streak) / 2, 1),
                'total_completions': row.total_completions
            })
        
        return streak_data
    
    async def _calculate_current_streak(self, habit_id: int) -> int:
        """Calculate current streak for a habit"""
        
        query = """
        WITH daily_completions AS (
            SELECT DATE(timestamp) as completion_date
            FROM logs 
            WHERE habit_id = :habit_id 
            AND action = 'completed'
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
    
    async def _calculate_best_streak(self, habit_id: int) -> int:
        """Calculate best streak ever for a habit"""
        
        query = """
        WITH daily_completions AS (
            SELECT DISTINCT DATE(timestamp) as completion_date
            FROM logs 
            WHERE habit_id = :habit_id 
            AND action = 'completed'
            ORDER BY completion_date
        ),
        streak_groups AS (
            SELECT 
                completion_date,
                completion_date - INTERVAL '1 day' * ROW_NUMBER() OVER (ORDER BY completion_date) as group_date
            FROM daily_completions
        ),
        streak_lengths AS (
            SELECT COUNT(*) as streak_length
            FROM streak_groups
            GROUP BY group_date
        )
        SELECT COALESCE(MAX(streak_length), 0) as best_streak
        FROM streak_lengths
        """
        
        result = await self.db.execute(text(query), {"habit_id": habit_id})
        row = result.first()
        return row.best_streak if row else 0
    
    async def export_analytics_data(self, user_id: int, format: str = 'json',
                                   time_range: str = '30d') -> bytes:
        """Export analytics data in specified format"""
        
        analytics_data = await self.get_comprehensive_analytics(user_id, time_range)
        
        if format.lower() == 'json':
            return json.dumps(analytics_data, indent=2, default=str).encode('utf-8')
        
        elif format.lower() == 'csv':
            # Create CSV export with multiple sheets worth of data
            csv_data = []
            
            # Completion trend
            trend_data = analytics_data.get('completion_trend', [])
            if trend_data:
                csv_data.append("# Completion Trend")
                csv_data.append("Date,Completion Rate,Completions,Total Attempts")
                for item in trend_data:
                    csv_data.append(f"{item['date']},{item['completion_rate']},{item['completions']},{item['total_attempts']}")
                csv_data.append("")
            
            # Category distribution
            category_data = analytics_data.get('category_distribution', [])
            if category_data:
                csv_data.append("# Category Distribution")
                csv_data.append("Category,Habit Count,Completions")
                for item in category_data:
                    csv_data.append(f"{item['name']},{item['count']},{item['completions']}")
                csv_data.append("")
            
            # Difficulty analysis
            difficulty_data = analytics_data.get('difficulty_analysis', [])
            if difficulty_data:
                csv_data.append("# Difficulty Analysis")
                csv_data.append("Difficulty,Habit Count,Success Rate,Completions")
                for item in difficulty_data:
                    csv_data.append(f"{item['difficulty']},{item['habit_count']},{item['success_rate']},{item['completions']}")
            
            return "\n".join(csv_data).encode('utf-8')
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# FastAPI endpoints for analytics
async def get_advanced_analytics(user_id: int, time_range: str = '30d',
                               metrics: str = '', db: Session = None) -> Dict:
    """Get comprehensive analytics data"""
    
    service = AdvancedAnalyticsService(db)
    selected_metrics = metrics.split(',') if metrics else None
    
    return await service.get_comprehensive_analytics(
        user_id=user_id,
        time_range=time_range,
        metrics=selected_metrics
    )


async def export_analytics(user_id: int, format: str = 'json',
                         time_range: str = '30d', db: Session = None) -> bytes:
    """Export analytics data"""
    
    service = AdvancedAnalyticsService(db)
    return await service.export_analytics_data(user_id, format, time_range)