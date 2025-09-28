"""
AI-Powered Habit Insights and Smart Recommendations System
Provides intelligent analytics, pattern detection, and personalized suggestions
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
import openai
from sqlalchemy.orm import Session
from sqlalchemy import text

from .models import Habit, Log, User
from .db import get_db


@dataclass
class HabitPattern:
    """Represents a detected habit pattern"""
    pattern_type: str  # 'streak', 'decline', 'inconsistent', 'cyclical'
    confidence: float  # 0.0 to 1.0
    description: str
    suggestions: List[str]
    supporting_data: Dict[str, Any]


@dataclass
class HabitInsight:
    """Individual habit insight"""
    habit_id: int
    insight_type: str
    title: str
    description: str
    actionable_suggestions: List[str]
    data_visualization: Dict[str, Any]
    priority_score: float  # 0.0 to 1.0


@dataclass
class SmartRecommendation:
    """AI-powered recommendation"""
    recommendation_type: str  # 'new_habit', 'habit_modification', 'timing', 'goal_adjustment'
    title: str
    description: str
    rationale: str
    confidence: float
    expected_impact: str
    implementation_steps: List[str]


class HabitAnalyzer:
    """Advanced analytics for habit tracking data"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.scaler = StandardScaler()
    
    async def analyze_user_patterns(self, user_id: int) -> List[HabitPattern]:
        """Analyze patterns in user's habit data"""
        
        patterns = []
        
        # Get user's habit data
        habits_data = await self._get_user_habit_data(user_id)
        
        if not habits_data:
            return patterns
        
        # Analyze each habit
        for habit_id, data in habits_data.items():
            habit_patterns = await self._analyze_single_habit(habit_id, data)
            patterns.extend(habit_patterns)
        
        return patterns
    
    async def _get_user_habit_data(self, user_id: int) -> Dict[int, Dict]:
        """Retrieve comprehensive habit data for a user"""
        
        query = """
        SELECT 
            h.id as habit_id,
            h.title,
            h.difficulty,
            h.cadence,
            h.status,
            h.created_at,
            l.timestamp,
            l.action,
            l.metadata
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id
        WHERE h.user_id = :user_id
        AND l.timestamp >= :start_date
        ORDER BY h.id, l.timestamp
        """
        
        start_date = datetime.now() - timedelta(days=90)  # 3 months of data
        
        result = await self.db.execute(
            text(query), 
            {"user_id": user_id, "start_date": start_date}
        )
        
        # Group data by habit
        habits_data = {}
        for row in result:
            habit_id = row.habit_id
            if habit_id not in habits_data:
                habits_data[habit_id] = {
                    'title': row.title,
                    'difficulty': row.difficulty,
                    'cadence': row.cadence,
                    'status': row.status,
                    'created_at': row.created_at,
                    'logs': []
                }
            
            if row.timestamp:  # Only add if log exists
                habits_data[habit_id]['logs'].append({
                    'timestamp': row.timestamp,
                    'action': row.action,
                    'metadata': json.loads(row.metadata or '{}')
                })
        
        return habits_data
    
    async def _analyze_single_habit(self, habit_id: int, data: Dict) -> List[HabitPattern]:
        """Analyze patterns for a single habit"""
        
        patterns = []
        logs = data['logs']
        
        if len(logs) < 5:  # Need minimum data for analysis
            return patterns
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Analyze completion patterns
        completion_pattern = await self._analyze_completion_pattern(df, data)
        if completion_pattern:
            patterns.append(completion_pattern)
        
        # Analyze timing patterns
        timing_pattern = await self._analyze_timing_pattern(df, data)
        if timing_pattern:
            patterns.append(timing_pattern)
        
        # Analyze streak patterns
        streak_pattern = await self._analyze_streak_pattern(df, data)
        if streak_pattern:
            patterns.append(streak_pattern)
        
        # Analyze cyclical patterns
        cyclical_pattern = await self._analyze_cyclical_pattern(df, data)
        if cyclical_pattern:
            patterns.append(cyclical_pattern)
        
        return patterns
    
    async def _analyze_completion_pattern(self, df: pd.DataFrame, habit_data: Dict) -> Optional[HabitPattern]:
        """Analyze completion rate patterns"""
        
        completion_logs = df[df['action'] == 'completed']
        
        if len(completion_logs) == 0:
            return HabitPattern(
                pattern_type='no_completions',
                confidence=1.0,
                description=f"No completions recorded for {habit_data['title']}",
                suggestions=[
                    "Start with just 1-2 minutes per day",
                    "Set a specific time for this habit",
                    "Pair it with an existing habit (habit stacking)"
                ],
                supporting_data={'completion_count': 0}
            )
        
        # Calculate completion rate over time
        total_days = (df['timestamp'].max() - df['timestamp'].min()).days + 1
        completion_rate = len(completion_logs) / total_days
        
        # Analyze trends
        completion_logs['week'] = completion_logs['timestamp'].dt.isocalendar().week
        weekly_completions = completion_logs.groupby('week').size()
        
        if len(weekly_completions) >= 3:
            # Calculate trend
            weeks = np.array(range(len(weekly_completions)))
            completions = weekly_completions.values
            slope = np.polyfit(weeks, completions, 1)[0]
            
            if slope > 0.5:
                return HabitPattern(
                    pattern_type='improving',
                    confidence=0.8,
                    description=f"Your {habit_data['title']} habit is showing steady improvement",
                    suggestions=[
                        "Keep up the momentum!",
                        "Consider increasing difficulty slightly",
                        "Track what's working and do more of it"
                    ],
                    supporting_data={
                        'trend_slope': slope,
                        'completion_rate': completion_rate,
                        'weekly_data': weekly_completions.to_dict()
                    }
                )
            elif slope < -0.5:
                return HabitPattern(
                    pattern_type='declining',
                    confidence=0.8,
                    description=f"Your {habit_data['title']} habit seems to be declining",
                    suggestions=[
                        "Reduce the difficulty temporarily",
                        "Identify what barriers are preventing completion",
                        "Consider changing the time of day you do this habit"
                    ],
                    supporting_data={
                        'trend_slope': slope,
                        'completion_rate': completion_rate,
                        'weekly_data': weekly_completions.to_dict()
                    }
                )
        
        return None
    
    async def _analyze_timing_pattern(self, df: pd.DataFrame, habit_data: Dict) -> Optional[HabitPattern]:
        """Analyze timing patterns in habit completion"""
        
        completion_logs = df[df['action'] == 'completed']
        
        if len(completion_logs) < 5:
            return None
        
        # Extract hour of day
        completion_logs['hour'] = completion_logs['timestamp'].dt.hour
        hour_counts = completion_logs['hour'].value_counts()
        
        # Find most common completion time
        peak_hour = hour_counts.index[0]
        peak_percentage = hour_counts.iloc[0] / len(completion_logs)
        
        if peak_percentage > 0.6:  # Strong timing pattern
            time_desc = self._hour_to_description(peak_hour)
            return HabitPattern(
                pattern_type='timing_consistent',
                confidence=peak_percentage,
                description=f"You consistently complete {habit_data['title']} in the {time_desc}",
                suggestions=[
                    f"Your {time_desc} timing works well - stick with it!",
                    "Set a daily reminder for this optimal time",
                    "Use this timing pattern for similar habits"
                ],
                supporting_data={
                    'peak_hour': peak_hour,
                    'peak_percentage': peak_percentage,
                    'hourly_distribution': hour_counts.to_dict()
                }
            )
        
        return None
    
    async def _analyze_streak_pattern(self, df: pd.DataFrame, habit_data: Dict) -> Optional[HabitPattern]:
        """Analyze streak patterns"""
        
        completion_logs = df[df['action'] == 'completed']
        
        if len(completion_logs) < 3:
            return None
        
        # Calculate streaks
        completion_logs['date'] = completion_logs['timestamp'].dt.date
        unique_dates = sorted(completion_logs['date'].unique())
        
        streaks = []
        current_streak = 1
        
        for i in range(1, len(unique_dates)):
            if (unique_dates[i] - unique_dates[i-1]).days == 1:
                current_streak += 1
            else:
                if current_streak > 1:
                    streaks.append(current_streak)
                current_streak = 1
        
        if current_streak > 1:
            streaks.append(current_streak)
        
        if streaks:
            max_streak = max(streaks)
            avg_streak = np.mean(streaks)
            
            if max_streak >= 7:
                return HabitPattern(
                    pattern_type='streak_achiever',
                    confidence=0.9,
                    description=f"Great job! Your longest streak for {habit_data['title']} is {max_streak} days",
                    suggestions=[
                        "Focus on maintaining consistency rather than perfection",
                        "Plan ahead for potential disruptions",
                        "Celebrate your streak milestones"
                    ],
                    supporting_data={
                        'max_streak': max_streak,
                        'avg_streak': avg_streak,
                        'total_streaks': len(streaks)
                    }
                )
        
        return None
    
    async def _analyze_cyclical_pattern(self, df: pd.DataFrame, habit_data: Dict) -> Optional[HabitPattern]:
        """Analyze cyclical patterns (weekly, monthly)"""
        
        completion_logs = df[df['action'] == 'completed']
        
        if len(completion_logs) < 14:  # Need at least 2 weeks
            return None
        
        # Analyze day of week patterns
        completion_logs['weekday'] = completion_logs['timestamp'].dt.day_name()
        weekday_counts = completion_logs['weekday'].value_counts()
        
        # Check for strong day-of-week preferences
        max_day = weekday_counts.index[0]
        max_percentage = weekday_counts.iloc[0] / len(completion_logs)
        
        if max_percentage > 0.4:  # Strong preference for specific day
            return HabitPattern(
                pattern_type='weekly_cyclical',
                confidence=max_percentage,
                description=f"You tend to complete {habit_data['title']} most often on {max_day}s",
                suggestions=[
                    f"Consider scheduling similar habits on {max_day}s",
                    "Use this natural rhythm to your advantage",
                    "Plan for lower motivation on other days"
                ],
                supporting_data={
                    'peak_day': max_day,
                    'peak_percentage': max_percentage,
                    'weekday_distribution': weekday_counts.to_dict()
                }
            )
        
        return None
    
    def _hour_to_description(self, hour: int) -> str:
        """Convert hour to descriptive time period"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"


class AIRecommendationEngine:
    """AI-powered recommendation engine for habit optimization"""
    
    def __init__(self, db_session: Session, openai_api_key: Optional[str] = None):
        self.db = db_session
        self.analyzer = HabitAnalyzer(db_session)
        if openai_api_key:
            openai.api_key = openai_api_key
    
    async def generate_insights(self, user_id: int) -> List[HabitInsight]:
        """Generate AI-powered insights for a user"""
        
        insights = []
        patterns = await self.analyzer.analyze_user_patterns(user_id)
        
        for pattern in patterns:
            insight = await self._pattern_to_insight(pattern)
            if insight:
                insights.append(insight)
        
        # Add performance-based insights
        performance_insights = await self._generate_performance_insights(user_id)
        insights.extend(performance_insights)
        
        # Sort by priority score
        insights.sort(key=lambda x: x.priority_score, reverse=True)
        
        return insights[:10]  # Return top 10 insights
    
    async def generate_recommendations(self, user_id: int) -> List[SmartRecommendation]:
        """Generate personalized recommendations"""
        
        recommendations = []
        
        # Get user data and patterns
        patterns = await self.analyzer.analyze_user_patterns(user_id)
        user_habits = await self._get_user_habits_summary(user_id)
        
        # Generate different types of recommendations
        habit_suggestions = await self._suggest_new_habits(user_habits, patterns)
        recommendations.extend(habit_suggestions)
        
        timing_suggestions = await self._suggest_timing_optimizations(patterns)
        recommendations.extend(timing_suggestions)
        
        goal_adjustments = await self._suggest_goal_adjustments(user_habits, patterns)
        recommendations.extend(goal_adjustments)
        
        # Use AI for advanced recommendations if available
        if openai.api_key:
            ai_recommendations = await self._generate_ai_recommendations(user_habits, patterns)
            recommendations.extend(ai_recommendations)
        
        # Sort by confidence and expected impact
        recommendations.sort(key=lambda x: x.confidence * 
                           (1.0 if x.expected_impact == 'high' else 
                            0.7 if x.expected_impact == 'medium' else 0.4), 
                           reverse=True)
        
        return recommendations[:8]  # Return top 8 recommendations
    
    async def _pattern_to_insight(self, pattern: HabitPattern) -> Optional[HabitInsight]:
        """Convert a pattern to an actionable insight"""
        
        priority_map = {
            'declining': 0.9,
            'no_completions': 0.8,
            'improving': 0.7,
            'streak_achiever': 0.6,
            'timing_consistent': 0.5,
            'weekly_cyclical': 0.4
        }
        
        if pattern.pattern_type not in priority_map:
            return None
        
        return HabitInsight(
            habit_id=pattern.supporting_data.get('habit_id', 0),
            insight_type=pattern.pattern_type,
            title=f"Pattern Detected: {pattern.pattern_type.replace('_', ' ').title()}",
            description=pattern.description,
            actionable_suggestions=pattern.suggestions,
            data_visualization={
                'chart_type': 'line' if 'trend' in pattern.pattern_type else 'bar',
                'data': pattern.supporting_data
            },
            priority_score=priority_map[pattern.pattern_type]
        )
    
    async def _generate_performance_insights(self, user_id: int) -> List[HabitInsight]:
        """Generate insights based on overall performance metrics"""
        
        insights = []
        
        # Get overall completion rate
        query = """
        SELECT 
            COUNT(CASE WHEN l.action = 'completed' THEN 1 END) as completions,
            COUNT(h.id) as total_habits,
            AVG(h.difficulty) as avg_difficulty
        FROM habits h
        LEFT JOIN logs l ON h.id = l.habit_id 
        WHERE h.user_id = :user_id
        AND h.created_at >= :start_date
        """
        
        start_date = datetime.now() - timedelta(days=30)
        result = await self.db.execute(text(query), {
            "user_id": user_id, 
            "start_date": start_date
        })
        
        row = result.first()
        if row and row.total_habits > 0:
            completion_rate = (row.completions or 0) / (row.total_habits * 30)  # Daily rate
            
            if completion_rate < 0.3:
                insights.append(HabitInsight(
                    habit_id=0,
                    insight_type='low_completion_rate',
                    title="Completion Rate Needs Attention",
                    description=f"Your overall habit completion rate is {completion_rate:.1%}",
                    actionable_suggestions=[
                        "Focus on just 1-2 key habits",
                        "Reduce difficulty of existing habits",
                        "Set more realistic daily goals"
                    ],
                    data_visualization={
                        'chart_type': 'gauge',
                        'data': {'completion_rate': completion_rate}
                    },
                    priority_score=0.95
                ))
        
        return insights
    
    async def _get_user_habits_summary(self, user_id: int) -> Dict:
        """Get summary of user's habits"""
        
        query = """
        SELECT 
            COUNT(*) as total_habits,
            AVG(difficulty) as avg_difficulty,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_habits,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_habits
        FROM habits 
        WHERE user_id = :user_id
        """
        
        result = await self.db.execute(text(query), {"user_id": user_id})
        row = result.first()
        
        return {
            'total_habits': row.total_habits or 0,
            'avg_difficulty': float(row.avg_difficulty or 0),
            'active_habits': row.active_habits or 0,
            'completed_habits': row.completed_habits or 0
        }
    
    async def _suggest_new_habits(self, user_summary: Dict, patterns: List[HabitPattern]) -> List[SmartRecommendation]:
        """Suggest new habits based on user patterns"""
        
        recommendations = []
        
        # If user has very few habits, suggest foundational ones
        if user_summary['total_habits'] < 3:
            recommendations.append(SmartRecommendation(
                recommendation_type='new_habit',
                title="Start with Morning Hydration",
                description="Build a foundation with a simple habit: drink a glass of water when you wake up",
                rationale="Simple habits with immediate rewards build confidence and create momentum",
                confidence=0.9,
                expected_impact='high',
                implementation_steps=[
                    "Place a glass of water by your bedside tonight",
                    "Drink it immediately upon waking",
                    "Track it for one week to build the habit loop"
                ]
            ))
        
        # If user is successful with timing patterns, suggest complementary habits
        timing_patterns = [p for p in patterns if p.pattern_type == 'timing_consistent']
        if timing_patterns:
            recommendations.append(SmartRecommendation(
                recommendation_type='new_habit',
                title="Stack Another Habit with Your Successful Timing",
                description="You have great timing consistency - use it to build another habit",
                rationale="Habit stacking leverages existing successful patterns",
                confidence=0.8,
                expected_impact='medium',
                implementation_steps=[
                    "Choose a 2-minute habit to add",
                    "Do it immediately after your existing successful habit",
                    "Keep the new habit very small initially"
                ]
            ))
        
        return recommendations
    
    async def _suggest_timing_optimizations(self, patterns: List[HabitPattern]) -> List[SmartRecommendation]:
        """Suggest timing optimizations based on patterns"""
        
        recommendations = []
        
        # Look for inconsistent timing patterns
        timing_patterns = [p for p in patterns if 'timing' in p.pattern_type]
        
        for pattern in timing_patterns:
            if pattern.confidence < 0.4:  # Inconsistent timing
                recommendations.append(SmartRecommendation(
                    recommendation_type='timing',
                    title="Establish Consistent Timing",
                    description="Your habit timing is inconsistent - establishing a routine could help",
                    rationale="Consistent timing reduces decision fatigue and builds automaticity",
                    confidence=0.7,
                    expected_impact='medium',
                    implementation_steps=[
                        "Choose one specific time for this habit",
                        "Set a daily reminder",
                        "Stick to the time for at least one week"
                    ]
                ))
        
        return recommendations
    
    async def _suggest_goal_adjustments(self, user_summary: Dict, patterns: List[HabitPattern]) -> List[SmartRecommendation]:
        """Suggest goal adjustments based on performance"""
        
        recommendations = []
        
        # If user has declining patterns, suggest reducing difficulty
        declining_patterns = [p for p in patterns if p.pattern_type == 'declining']
        
        if declining_patterns:
            recommendations.append(SmartRecommendation(
                recommendation_type='goal_adjustment',
                title="Temporarily Reduce Habit Difficulty",
                description="Some habits are showing decline - reducing difficulty can restore momentum",
                rationale="Lower barriers to entry increase consistency and build confidence",
                confidence=0.8,
                expected_impact='high',
                implementation_steps=[
                    "Identify your most challenging habits",
                    "Reduce the goal by 50% (e.g., 20 minutes -> 10 minutes)",
                    "Focus on consistency over intensity for 2 weeks"
                ]
            ))
        
        return recommendations
    
    async def _generate_ai_recommendations(self, user_summary: Dict, patterns: List[HabitPattern]) -> List[SmartRecommendation]:
        """Generate advanced recommendations using OpenAI"""
        
        if not openai.api_key:
            return []
        
        # Prepare context for AI
        context = {
            'user_summary': user_summary,
            'patterns': [asdict(p) for p in patterns]
        }
        
        prompt = f"""
        Based on the following habit tracking data, provide 2-3 specific, actionable recommendations:
        
        User Summary: {json.dumps(user_summary, indent=2)}
        
        Detected Patterns: {json.dumps([asdict(p) for p in patterns], indent=2, default=str)}
        
        Please provide recommendations in the following JSON format:
        {{
            "recommendations": [
                {{
                    "title": "specific recommendation title",
                    "description": "detailed description",
                    "rationale": "why this will help",
                    "confidence": 0.8,
                    "expected_impact": "high/medium/low",
                    "implementation_steps": ["step 1", "step 2", "step 3"]
                }}
            ]
        }}
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are a habit formation expert providing personalized recommendations."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=1000,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            
            recommendations = []
            for rec in result.get('recommendations', []):
                recommendations.append(SmartRecommendation(
                    recommendation_type='ai_generated',
                    title=rec['title'],
                    description=rec['description'],
                    rationale=rec['rationale'],
                    confidence=rec['confidence'],
                    expected_impact=rec['expected_impact'],
                    implementation_steps=rec['implementation_steps']
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {e}")
            return []


# FastAPI endpoints for insights and recommendations
async def get_user_insights(user_id: int, db: Session) -> List[Dict]:
    """Get insights for a user"""
    
    engine = AIRecommendationEngine(db)
    insights = await engine.generate_insights(user_id)
    
    return [asdict(insight) for insight in insights]


async def get_user_recommendations(user_id: int, db: Session) -> List[Dict]:
    """Get recommendations for a user"""
    
    engine = AIRecommendationEngine(db)
    recommendations = await engine.generate_recommendations(user_id)
    
    return [asdict(rec) for rec in recommendations]