"""
OpenAPI/Swagger documentation configuration for LifeRPG API.
Provides comprehensive API documentation including AI endpoints.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi_schema(app: FastAPI):
    """Generate custom OpenAPI schema with comprehensive AI documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="LifeRPG API - AI-Powered Habit Management",
        version="3.0.0",
        description="""
        ## 🧙‍♂️ The AI-Powered Habit Management Platform

        LifeRPG transforms daily habits into magical achievements using cutting-edge AI.
        
        ### 🤖 AI Features
        - **Natural Language Processing**: Create habits using plain English
        - **Predictive Analytics**: AI forecasts habit success probability  
        - **Voice & Image Input**: Multimodal interaction capabilities
        - **Smart Suggestions**: Personalized recommendations
        - **Local Processing**: 100% privacy-focused AI (no external APIs)

        ### 🔒 Authentication
        Most endpoints require JWT authentication. Get your token from `/auth/login`.

        ### 📊 Rate Limits
        - AI endpoints: 60 requests per minute
        - Standard endpoints: 100 requests per minute
        - Authenticated users get higher limits

        ### 🚀 Getting Started
        1. Register: `POST /auth/register`
        2. Login: `POST /auth/login` 
        3. Create habits: `POST /ai/habits/create-natural`
        4. Get predictions: `GET /ai/habits/predict-success/{habit_id}`

        ### 💡 Examples
        **Natural Language Habit Creation:**
        ```json
        {
          "text": "I want to drink 8 glasses of water every day"
        }
        ```
        
        **Response:**
        ```json
        {
          "name": "Drink Water",
          "frequency": "daily",
          "target": 8,
          "unit": "glasses",
          "category": "health"
        }
        ```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": "User registration, login, and token management"
            },
            {
                "name": "Habits",
                "description": "Core habit CRUD operations"
            },
            {
                "name": "AI Habits",
                "description": "🤖 AI-powered habit management features",
                "externalDocs": {
                    "description": "AI Documentation",
                    "url": "https://github.com/TLimoges33/LifeRPG/blob/master/PHASE_3_AI_README.md"
                }
            },
            {
                "name": "Analytics", 
                "description": "📊 Habit analytics and insights"
            },
            {
                "name": "Social",
                "description": "👥 Social features and leaderboards"
            },
            {
                "name": "Gamification",
                "description": "🎮 XP, levels, achievements, and RPG features"
            },
            {
                "name": "Health",
                "description": "🏥 Health checks and system status"
            }
        ]
    )

    # Add AI-specific schema components
    openapi_schema["components"]["schemas"].update({
        "HabitParseRequest": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Natural language description of the habit",
                    "example": "I want to exercise for 30 minutes every morning"
                }
            },
            "required": ["text"]
        },
        "HabitParseResponse": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Extracted habit name",
                    "example": "Morning Exercise"
                },
                "frequency": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly", "custom"],
                    "description": "How often to perform the habit"
                },
                "category": {
                    "type": "string",
                    "description": "AI-determined category",
                    "example": "fitness"
                },
                "target": {
                    "type": "integer", 
                    "description": "Target amount (if applicable)",
                    "example": 30
                },
                "unit": {
                    "type": "string",
                    "description": "Unit of measurement",
                    "example": "minutes"
                },
                "confidence": {
                    "type": "number",
                    "format": "float",
                    "description": "AI confidence in parsing (0.0-1.0)",
                    "example": 0.92
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "AI suggestions for improvement"
                }
            }
        },
        "AISuccessPrediction": {
            "type": "object", 
            "properties": {
                "probability": {
                    "type": "number",
                    "format": "float",
                    "description": "Success probability (0.0-1.0)",
                    "example": 0.78
                },
                "confidence": {
                    "type": "number",
                    "format": "float", 
                    "description": "Prediction confidence",
                    "example": 0.85
                },
                "factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key factors influencing prediction"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "AI recommendations to improve success"
                }
            }
        },
        "AISuggestion": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Suggestion text",
                    "example": "Try adding a 5-minute warm-up routine"
                },
                "category": {
                    "type": "string",
                    "description": "Suggestion category",
                    "example": "fitness"
                },
                "confidence": {
                    "type": "number",
                    "format": "float",
                    "description": "AI confidence in suggestion",
                    "example": 0.89
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Suggested priority level"
                }
            }
        },
        "VoiceCommandRequest": {
            "type": "object",
            "properties": {
                "audio_data": {
                    "type": "string",
                    "format": "base64",
                    "description": "Base64 encoded audio data"
                },
                "format": {
                    "type": "string",
                    "enum": ["wav", "mp3", "webm"],
                    "description": "Audio format"
                }
            },
            "required": ["audio_data", "format"]
        },
        "ImageCheckinRequest": {
            "type": "object",
            "properties": {
                "image_data": {
                    "type": "string",
                    "format": "base64", 
                    "description": "Base64 encoded image data"
                },
                "habit_id": {
                    "type": "integer",
                    "description": "Optional habit ID to match against"
                }
            },
            "required": ["image_data"]
        },
        "PatternAnalysis": {
            "type": "object",
            "properties": {
                "patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Identified behavioral patterns"
                },
                "trends": {
                    "type": "object",
                    "description": "Statistical trends in habit completion"
                },
                "insights": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "AI-generated insights"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Personalized recommendations"
                }
            }
        }
    })

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login"
        }
    }

    # Add AI endpoints documentation examples
    openapi_schema["paths"]["/api/v1/ai/habits/create-natural"] = {
        "post": {
            "tags": ["AI Habits"],
            "summary": "🤖 Create habit from natural language",
            "description": """
            Parse natural language text into a structured habit using AI.
            
            **Examples:**
            - "I want to drink water every morning"
            - "Exercise for 30 minutes 3 times a week"  
            - "Read 20 pages before bed daily"
            
            The AI will extract:
            - Habit name and description
            - Frequency and timing
            - Target amounts and units
            - Appropriate category
            """,
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HabitParseRequest"}
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Successfully parsed habit",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/HabitParseResponse"}
                        }
                    }
                },
                "400": {
                    "description": "Invalid input text"
                },
                "429": {
                    "description": "Rate limit exceeded"
                },
                "503": {
                    "description": "AI service unavailable"
                }
            },
            "security": [{"BearerAuth": []}]
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_docs(app: FastAPI):
    """Set up comprehensive API documentation."""
    
    # Custom OpenAPI schema
    app.openapi = lambda: custom_openapi_schema(app)
    
    # Add metadata
    app.title = "LifeRPG API"
    app.description = "🧙‍♂️ AI-Powered Habit Management Platform"
    app.version = "3.0.0"
    app.terms_of_service = "https://liferpg.com/terms"
    app.contact = {
        "name": "LifeRPG Support",
        "url": "https://github.com/TLimoges33/LifeRPG",
        "email": "support@liferpg.com"
    }
    app.license_info = {
        "name": "MIT License",
        "url": "https://github.com/TLimoges33/LifeRPG/blob/master/LICENSE"
    }
    
    return app


# Add this to your main app.py file:
# from api_docs import setup_api_docs
# app = setup_api_docs(app)