"""
AI Assistant backend for LifeRPG Phase 3
- Natural language habit creation
- Smart suggestions
- Predictive analytics endpoints
- Voice/image recognition stubs
"""

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any
import re

from db import get_db
from models import User, Habit, Log
from auth import get_current_user
from huggingface_ai import huggingface_ai

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/habits/nlp-create")
async def nlp_create_habit(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a habit from a natural language prompt using HuggingFace AI."""
    data = await request.json()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return JSONResponse({'error': 'Prompt required'}, status_code=400)

    try:
        # Use HuggingFace AI to parse the habit
        habit_data = await huggingface_ai.parse_habit_from_text(prompt)
        
        # Create habit with parsed data
        habit = Habit(
            user_id=current_user.id,
            title=habit_data.get('title', prompt),
            cadence=habit_data.get('cadence', 'daily'),
            due_time=habit_data.get('due_time'),
            difficulty=habit_data.get('difficulty', 1),
            category=habit_data.get('category'),
            created_at=datetime.now(),
            is_active=True
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)
        
        return {
            'success': True, 
            'habit': {
                'id': habit.id, 
                'title': habit.title, 
                'cadence': habit.cadence, 
                'due_time': habit.due_time,
                'difficulty': habit.difficulty,
                'category': habit.category
            },
            'ai_insights': {
                'confidence': habit_data.get('confidence', 0.8),
                'source': habit_data.get('source', 'ai_parser')
            }
        }
        
    except Exception as e:
        # Fallback to simple parsing
        habit = Habit(
            user_id=current_user.id,
            title=prompt,
            cadence='daily',
            created_at=datetime.now(),
            is_active=True
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)
        
        return {
            'success': True, 
            'habit': {
                'id': habit.id, 
                'title': habit.title, 
                'cadence': habit.cadence
            },
            'ai_insights': {
                'confidence': 0.5,
                'source': 'fallback_parser',
                'note': 'AI parsing failed, used simple parsing'
            }
        }

# --- Smart Suggestions ---

@router.get("/habits/suggestions")
async def ai_habit_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered habit suggestions using HuggingFace."""
    try:
        # Get user's existing habits
        user_habits_query = db.query(Habit).filter(
            Habit.user_id == current_user.id,
            Habit.is_active.is_(True)
        ).all()
        
        user_habits = [habit.title for habit in user_habits_query]
        user_data = {
            'total_habits': len(user_habits),
            'user_id': current_user.id
        }
        
        # Use HuggingFace AI for suggestions
        suggestions = await huggingface_ai.get_habit_suggestions(user_habits, user_data)
        
        return {'suggestions': suggestions}
        
    except Exception as e:
        # Fallback to simple suggestions
        return {
            'suggestions': [
                'Drink a glass of water every morning',
                'Take a 10-minute walk after lunch',
                'Read for 15 minutes before bed'
            ],
            'note': 'Using fallback suggestions'
        }


@router.get("/habits/predict-success")
async def predict_habit_success(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict habit success using AI analytics."""
    try:
        # Get habit data
        habit = db.query(Habit).filter(
            Habit.id == habit_id,
            Habit.user_id == current_user.id
        ).first()
        
        if not habit:
            return JSONResponse({'error': 'Habit not found'}, status_code=404)
        
        # Get user's habit history
        user_logs = db.query(Log).filter(Log.user_id == current_user.id).all()
        user_history = [
            {
                'completed': log.action == 'complete',
                'habit_id': log.habit_id,
                'timestamp': log.timestamp
            }
            for log in user_logs
        ]
        
        # Use HuggingFace AI for prediction
        habit_data = {
            'title': habit.title,
            'difficulty': habit.difficulty or 1,
            'category': habit.category,
            'cadence': habit.cadence
        }
        
        prediction = await huggingface_ai.predict_habit_success(habit_data, user_history)
        
        return {
            'habit_id': habit_id,
            'prediction': prediction
        }
        
    except Exception as e:
        # Fallback prediction
        return {
            'habit_id': habit_id,
            'prediction': {
                'success_probability': 0.75,
                'confidence': 0.5,
                'insights': ['Prediction using fallback method'],
                'recommended_adjustments': []
            },
            'note': 'Using fallback prediction'
        }


@router.get("/habits/analyze-patterns")
async def analyze_habit_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze user's habit patterns using AI."""
    try:
        analysis = await huggingface_ai.analyze_habit_patterns(db, current_user.id)
        return analysis
    except Exception as e:
        return {
            'patterns': {},
            'insights': ['Pattern analysis temporarily unavailable'],
            'recommendations': ['Try creating habits with specific times'],
            'note': 'Using fallback analysis'
        }

# --- Voice/Image Recognition Stubs ---
@router.post("/habits/voice-command")
async def process_voice_command(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process voice commands for habit management."""
    try:
        # In a real implementation, you would:
        # 1. Extract audio file from form data
        # 2. Use speech-to-text (like OpenAI Whisper or Google Speech-to-Text)
        # 3. Process the text with NLP
        # 4. Execute the appropriate action
        
        # For now, return a simulated response
        return {
            'transcript': 'Voice command received successfully!',
            'action': 'processed',
            'message': ('Voice processing with HuggingFace '
                        'Whisper coming soon!'),
            'confidence': 0.85
        }
    except Exception as e:
        return {
            'transcript': 'Voice processing failed',
            'error': str(e),
            'message': 'Voice recognition temporarily unavailable'
        }


@router.post("/habits/image-checkin")
async def process_image_checkin(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process image uploads for habit check-ins."""
    try:
        # In a real implementation, you would:
        # 1. Extract image file from form data
        # 2. Use computer vision models (like CLIP, YOLO, or custom models)
        # 3. Analyze the image content
        # 4. Match with user's habits and complete if appropriate
        
        # Simulate image processing
        detected_items = [
            'workout equipment',
            'healthy food',
            'book',
            'meditation cushion',
            'water bottle'
        ]
        
        return {
            'message': 'Image processed successfully!',
            'detected_items': detected_items,
            'confidence': 0.92,
            'habit_matched': True,
            'habit_id': 1,
            'habit_completed': True,
            'note': 'Image recognition with HuggingFace CLIP coming soon!'
        }
    except Exception as e:
        return {
            'message': 'Image processing failed',
            'error': str(e),
            'detected_items': [],
            'confidence': 0.0
        }
