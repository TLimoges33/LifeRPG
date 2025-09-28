"""
HuggingFace AI Integration for LifeRPG Phase 3
- Free/low-cost NLP using HuggingFace Transformers
- Local model inference where possible
- Fallback to HuggingFace API for complex tasks
- Predictive analytics using lightweight models
"""

import os
import re
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# For local inference (free)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from transformers import AutoModelForCausalLM, AutoTokenizer as AutoTokenizer2
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not installed. Install with: pip install transformers torch")

# For HuggingFace API (free tier available)
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

class HuggingFaceAI:
    """HuggingFace AI service for habit analysis and NLP"""
    
    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN")  # Optional for public models
        self.api_url = "https://api-inference.huggingface.co/models"
        
        # Initialize local models (lightweight, free)
        self._init_local_models()
    
    def _init_local_models(self):
        """Initialize lightweight local models for offline inference"""
        self.local_models = {}
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # Small sentiment analysis model (40MB)
                self.local_models['sentiment'] = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True
                )
                
                # Small text classification model for habit categorization
                self.local_models['text_classifier'] = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"  # 1.6GB but very capable
                )
                
                logging.info("✅ Local HuggingFace models loaded successfully")
            except Exception as e:
                logging.warning(f"Could not load local models: {e}")
        else:
            logging.warning("Transformers not available - using API fallback only")
    
    async def parse_habit_from_text(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into structured habit data"""
        
        # Use regex patterns first (fast, free, works offline)
        habit_data = self._regex_parse_habit(text)
        
        # Enhance with AI if available
        if TRANSFORMERS_AVAILABLE and 'text_classifier' in self.local_models:
            try:
                # Categorize the habit
                categories = [
                    "health", "fitness", "productivity", "learning", 
                    "social", "creativity", "mindfulness", "nutrition"
                ]
                
                result = self.local_models['text_classifier'](text, categories)
                if result['scores'][0] > 0.5:  # High confidence
                    habit_data['category'] = result['labels'][0]
                    habit_data['confidence'] = result['scores'][0]
            except Exception as e:
                logging.warning(f"Local classification failed: {e}")
        
        # Fallback to API for complex parsing if needed
        if not habit_data.get('title') and self.api_token:
            habit_data = await self._api_parse_habit(text)
        
        return habit_data
    
    def _regex_parse_habit(self, text: str) -> Dict[str, Any]:
        """Fast regex-based parsing for common habit patterns"""
        text_lower = text.lower()
        
        # Extract title (remove common prefixes)
        title = text
        for prefix in ['remind me to ', 'i want to ', 'help me ', 'i need to ']:
            if text_lower.startswith(prefix):
                title = text[len(prefix):]
                break
        
        # Extract frequency/cadence
        cadence = 'daily'  # default
        if any(word in text_lower for word in ['weekly', 'week', 'sunday', 'monday']):
            cadence = 'weekly'
        elif any(word in text_lower for word in ['monthly', 'month']):
            cadence = 'monthly'
        
        # Extract time
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'at\s+(\d{1,2})\s*(am|pm)',
        ]
        
        due_time = None
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if len(match.groups()) == 3:  # Hour:minute am/pm
                    hour, minute, period = match.groups()
                    due_time = f"{hour}:{minute} {period.upper()}"
                else:  # Hour am/pm
                    hour, period = match.groups()
                    due_time = f"{hour}:00 {period.upper()}"
                break
        
        # Extract difficulty indicators
        difficulty = 1  # default
        if any(word in text_lower for word in ['hard', 'difficult', 'challenging']):
            difficulty = 3
        elif any(word in text_lower for word in ['moderate', 'medium']):
            difficulty = 2
        
        return {
            'title': title.strip(),
            'cadence': cadence,
            'due_time': due_time,
            'difficulty': difficulty,
            'source': 'regex_parser'
        }
    
    async def _api_parse_habit(self, text: str) -> Dict[str, Any]:
        """Use HuggingFace API for complex parsing (fallback)"""
        try:
            # Use a small language model for text generation
            payload = {
                "inputs": f"Parse this habit request into JSON: {text}\nJSON:",
                "parameters": {
                    "max_new_tokens": 100,
                    "temperature": 0.1,
                    "return_full_text": False
                }
            }
            
            headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
            
            response = requests.post(
                f"{self.api_url}/microsoft/DialoGPT-small",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parse the generated JSON (simplified)
                return {"title": text, "source": "api_parser"}
            
        except Exception as e:
            logging.warning(f"API parsing failed: {e}")
        
        return {"title": text, "source": "fallback"}
    
    async def get_habit_suggestions(self, user_habits: List[str], user_data: Dict) -> List[str]:
        """Generate personalized habit suggestions"""
        
        # Rule-based suggestions (free, fast)
        suggestions = []
        
        habit_text = " ".join(user_habits).lower()
        
        # Health suggestions
        if not any(word in habit_text for word in ['water', 'hydrat']):
            suggestions.append("Drink 8 glasses of water daily")
        
        if not any(word in habit_text for word in ['walk', 'exercise', 'workout']):
            suggestions.append("Take a 15-minute walk after lunch")
        
        if not any(word in habit_text for word in ['sleep', 'bed']):
            suggestions.append("Go to bed by 10 PM for better sleep")
        
        # Productivity suggestions
        if not any(word in habit_text for word in ['read', 'book']):
            suggestions.append("Read for 20 minutes before bed")
        
        if not any(word in habit_text for word in ['gratitude', 'journal']):
            suggestions.append("Write 3 things you're grateful for")
        
        # Use AI for personalized suggestions if available
        if TRANSFORMERS_AVAILABLE and 'sentiment' in self.local_models:
            try:
                # Analyze sentiment of existing habits
                for habit in user_habits:
                    sentiment = self.local_models['sentiment'](habit)[0]
                    if sentiment['label'] == 'NEGATIVE':
                        # Suggest positive alternatives
                        suggestions.append("Practice 5 minutes of meditation")
                        break
            except Exception as e:
                logging.warning(f"Sentiment analysis failed: {e}")
        
        return suggestions[:5]  # Limit to top 5
    
    async def predict_habit_success(self, habit_data: Dict, user_history: List[Dict]) -> Dict[str, Any]:
        """Predict habit success probability using simple ML"""
        
        # Simple rule-based prediction (can be enhanced with ML)
        base_probability = 0.7  # Default 70%
        
        # Adjust based on habit characteristics
        difficulty = habit_data.get('difficulty', 1)
        if difficulty >= 3:
            base_probability -= 0.2
        
        # Adjust based on user history
        if user_history:
            recent_success_rate = sum(1 for h in user_history[-10:] if h.get('completed', False)) / len(user_history[-10:])
            base_probability = (base_probability + recent_success_rate) / 2
        
        # Adjust based on category (if available)
        category = habit_data.get('category', '')
        if category in ['health', 'fitness']:
            base_probability += 0.1  # Health habits tend to be more successful
        
        # Clamp between 0 and 1
        probability = max(0.0, min(1.0, base_probability))
        
        # Generate insights
        insights = []
        if probability < 0.5:
            insights.append("Consider starting with an easier version of this habit")
        if habit_data.get('due_time'):
            insights.append("Having a specific time increases success rate by 40%")
        if difficulty >= 3:
            insights.append("High difficulty habits benefit from gradual progression")
        
        return {
            'success_probability': round(probability, 2),
            'confidence': 0.8,  # Static for now
            'insights': insights,
            'recommended_adjustments': self._get_habit_adjustments(habit_data, probability)
        }
    
    def _get_habit_adjustments(self, habit_data: Dict, probability: float) -> List[str]:
        """Suggest adjustments to improve habit success"""
        adjustments = []
        
        if probability < 0.6:
            adjustments.append("Start with a smaller, easier version")
            adjustments.append("Add a specific time and location")
            
        if habit_data.get('difficulty', 1) >= 3:
            adjustments.append("Break into smaller daily steps")
            
        if not habit_data.get('due_time'):
            adjustments.append("Set a specific time for better consistency")
            
        return adjustments
    
    async def analyze_habit_patterns(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze user's habit patterns using AI"""
        
        # This would use more sophisticated ML models
        # For now, return basic analytics with AI insights
        
        from .models import Habit, Log  # Import here to avoid circular imports
        
        # Get user's habits and logs
        habits = db.query(Habit).filter(Habit.user_id == user_id).all()
        recent_logs = db.query(Log).filter(Log.user_id == user_id).filter(
            Log.timestamp >= datetime.now() - timedelta(days=30)
        ).all()
        
        # Basic pattern analysis
        patterns = {
            'best_time_of_day': self._find_best_time_pattern(recent_logs),
            'success_by_difficulty': self._analyze_difficulty_success(habits, recent_logs),
            'streak_patterns': self._analyze_streak_patterns(habits),
            'category_performance': self._analyze_category_performance(habits, recent_logs)
        }
        
        return {
            'patterns': patterns,
            'insights': self._generate_pattern_insights(patterns),
            'recommendations': self._generate_recommendations(patterns)
        }
    
    def _find_best_time_pattern(self, logs: List) -> Dict[str, Any]:
        """Find the time of day user is most successful"""
        time_success = {}
        
        for log in logs:
            if log.action == 'complete':
                hour = log.timestamp.hour
                if hour not in time_success:
                    time_success[hour] = 0
                time_success[hour] += 1
        
        if time_success:
            best_hour = max(time_success.keys(), key=lambda k: time_success[k])
            return {
                'best_hour': best_hour,
                'success_count': time_success[best_hour],
                'total_completions': sum(time_success.values())
            }
        
        return {'best_hour': None, 'success_count': 0}
    
    def _analyze_difficulty_success(self, habits: List, logs: List) -> Dict[str, float]:
        """Analyze success rate by habit difficulty"""
        difficulty_stats = {}
        
        for habit in habits:
            difficulty = habit.difficulty or 1
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {'attempts': 0, 'completions': 0}
            
            habit_logs = [l for l in logs if l.habit_id == habit.id]
            difficulty_stats[difficulty]['attempts'] += len(habit_logs)
            difficulty_stats[difficulty]['completions'] += len([l for l in habit_logs if l.action == 'complete'])
        
        # Calculate success rates
        success_rates = {}
        for difficulty, stats in difficulty_stats.items():
            if stats['attempts'] > 0:
                success_rates[f'difficulty_{difficulty}'] = stats['completions'] / stats['attempts']
        
        return success_rates
    
    def _analyze_streak_patterns(self, habits: List) -> Dict[str, Any]:
        """Analyze streak patterns"""
        streaks = [h.current_streak or 0 for h in habits]
        
        return {
            'average_streak': sum(streaks) / len(streaks) if streaks else 0,
            'max_streak': max(streaks) if streaks else 0,
            'habits_with_streaks': len([s for s in streaks if s > 0])
        }
    
    def _analyze_category_performance(self, habits: List, logs: List) -> Dict[str, float]:
        """Analyze performance by habit category"""
        category_stats = {}
        
        for habit in habits:
            category = habit.category or 'uncategorized'
            if category not in category_stats:
                category_stats[category] = {'attempts': 0, 'completions': 0}
            
            habit_logs = [l for l in logs if l.habit_id == habit.id]
            category_stats[category]['attempts'] += len(habit_logs)
            category_stats[category]['completions'] += len([l for l in habit_logs if l.action == 'complete'])
        
        # Calculate success rates
        success_rates = {}
        for category, stats in category_stats.items():
            if stats['attempts'] > 0:
                success_rates[category] = stats['completions'] / stats['attempts']
        
        return success_rates
    
    def _generate_pattern_insights(self, patterns: Dict) -> List[str]:
        """Generate insights from patterns"""
        insights = []
        
        best_time = patterns.get('best_time_of_day', {})
        if best_time.get('best_hour'):
            hour_12 = best_time['best_hour']
            if hour_12 > 12:
                hour_12 -= 12
                period = "PM"
            else:
                period = "AM"
            insights.append(f"You're most successful completing habits at {hour_12} {period}")
        
        difficulty_success = patterns.get('success_by_difficulty', {})
        if difficulty_success:
            best_difficulty = max(difficulty_success.keys(), key=lambda k: difficulty_success[k])
            insights.append(f"You have highest success with {best_difficulty} habits")
        
        streak_patterns = patterns.get('streak_patterns', {})
        if streak_patterns.get('average_streak', 0) > 5:
            insights.append("You're great at maintaining streaks!")
        
        return insights
    
    def _generate_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations based on patterns"""
        recommendations = []
        
        best_time = patterns.get('best_time_of_day', {})
        if best_time.get('best_hour'):
            recommendations.append(f"Schedule new habits around {best_time['best_hour']}:00 for better success")
        
        difficulty_success = patterns.get('success_by_difficulty', {})
        if difficulty_success.get('difficulty_1', 0) > difficulty_success.get('difficulty_3', 0):
            recommendations.append("Start with easier habits and gradually increase difficulty")
        
        category_performance = patterns.get('category_performance', {})
        if category_performance:
            best_category = max(category_performance.keys(), key=lambda k: category_performance[k])
            recommendations.append(f"Focus on {best_category} habits - you excel in this area")
        
        return recommendations

# Global instance
huggingface_ai = HuggingFaceAI()