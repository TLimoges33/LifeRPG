#!/usr/bin/env python3
"""
Quick test API for Phase 3 AI features
Simulates the AI assistant endpoints
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from datetime import datetime
from huggingface_ai import HuggingFaceAI

app = FastAPI(title="LifeRPG AI Test API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI service
ai_service = HuggingFaceAI()

@app.post("/api/v1/ai/habits/nlp-create")
async def nlp_create_habit(request: Request):
    """Create a habit from natural language using AI."""
    try:
        data = await request.json()
        text = data.get('text', '')
        
        if not text:
            return {'error': 'No text provided'}
        
        # Parse habit using AI
        result = await ai_service.parse_habit_from_text(text)
        
        return {
            'success': True,
            'habit': result,
            'message': f'Successfully parsed habit: "{result.get("title", "Unknown")}"',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to parse habit'
        }


@app.get("/api/v1/ai/habits/suggestions")
async def get_ai_suggestions():
    """Get AI-powered habit suggestions."""
    return {
        'suggestions': [
            {
                'title': 'Drink 8 glasses of water daily',
                'category': 'health',
                'difficulty': 1,
                'reason': 'Based on popular health recommendations'
            },
            {
                'title': 'Read for 15 minutes before bed',
                'category': 'learning',
                'difficulty': 1,
                'reason': 'Improves sleep quality and knowledge'
            },
            {
                'title': 'Take a 10-minute walk after lunch',
                'category': 'fitness',
                'difficulty': 1,
                'reason': 'Boosts afternoon energy and aids digestion'
            }
        ],
        'timestamp': datetime.now().isoformat()
    }


@app.get("/api/v1/ai/habits/predict-success")
async def predict_success():
    """Predict habit success probability."""
    return {
        'predictions': [
            {
                'habit_id': 1,
                'habit_name': 'Morning Exercise',
                'success_probability': 0.85,
                'factors': ['consistent morning routine', 'past success pattern'],
                'recommendation': 'Continue current approach - high success probability'
            },
            {
                'habit_id': 2,
                'habit_name': 'Evening Reading',
                'success_probability': 0.65,
                'factors': ['variable evening schedule', 'high motivation'],
                'recommendation': 'Set specific reading time to improve consistency'
            }
        ],
        'timestamp': datetime.now().isoformat()
    }


@app.post("/api/v1/ai/habits/voice-command")
async def process_voice_command(request: Request):
    """Process voice commands for habit management."""
    try:
        # In a real implementation, extract audio file and process
        return {
            'transcript': 'Voice command received successfully!',
            'action': 'processed',
            'message': 'Voice processing with HuggingFace Whisper ready!',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'transcript': 'Voice processing failed',
            'error': str(e),
            'message': 'Voice recognition temporarily unavailable'
        }


@app.post("/api/v1/ai/habits/image-checkin")
async def process_image_checkin(request: Request):
    """Process image uploads for habit check-ins."""
    try:
        # In a real implementation, extract and analyze image
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
            'note': 'Image recognition with HuggingFace CLIP ready!',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'message': 'Image processing failed',
            'error': str(e),
            'detected_items': [],
            'confidence': 0.0
        }


@app.get("/api/v1/ai/analytics/patterns")
async def get_pattern_analysis():
    """Get AI-powered habit pattern analysis."""
    return {
        'patterns': [
            {
                'pattern': 'Morning habits have 85% higher completion rate',
                'confidence': 0.92,
                'recommendation': 'Schedule important habits in the morning'
            },
            {
                'pattern': 'Weekend completion drops by 30%',
                'confidence': 0.78,
                'recommendation': 'Create specific weekend routines'
            },
            {
                'pattern': 'Habit chains increase success by 40%',
                'confidence': 0.88,
                'recommendation': 'Link new habits to existing ones'
            }
        ],
        'insights': [
            'You perform best with 3-5 habits maximum',
            'Visual reminders increase completion by 25%',
            'Social accountability boosts success rate'
        ],
        'timestamp': datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """API status endpoint."""
    return {
        'service': 'LifeRPG AI Test API',
        'version': '3.0.0',
        'status': 'running',
        'ai_models_loaded': len(ai_service.local_models) if hasattr(ai_service, 'local_models') else 0,
        'endpoints': [
            '/api/v1/ai/habits/nlp-create',
            '/api/v1/ai/habits/suggestions',
            '/api/v1/ai/habits/predict-success',
            '/api/v1/ai/habits/voice-command',
            '/api/v1/ai/habits/image-checkin',
            '/api/v1/ai/analytics/patterns'
        ],
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("🚀 Starting LifeRPG AI Test API...")
    print("🤖 AI Features: Natural Language Processing, Predictive Analytics, Voice/Image Support")
    print("📡 Access: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)