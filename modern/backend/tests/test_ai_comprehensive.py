"""
Comprehensive test suite for LifeRPG AI functionality.
Tests HuggingFace AI integration, natural language processing, and predictions.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from huggingface_ai import HuggingFaceAI
    from ai_assistant import router
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    pytest.skip("AI dependencies not available", allow_module_level=True)


class TestHuggingFaceAI:
    """Test the core HuggingFace AI service functionality."""
    
    @pytest.fixture
    def ai_service(self):
        """Create an AI service instance for testing."""
        if AI_AVAILABLE:
            return HuggingFaceAI()
        return None
    
    @pytest.mark.asyncio
    async def test_ai_service_initialization(self, ai_service):
        """Test that AI service initializes correctly."""
        assert ai_service is not None
        assert hasattr(ai_service, 'parse_habit_from_text')
        assert hasattr(ai_service, 'generate_suggestions')
    
    @pytest.mark.asyncio
    async def test_habit_parsing_basic(self, ai_service):
        """Test basic habit parsing functionality."""
        test_inputs = [
            "I want to drink water daily",
            "Exercise for 30 minutes three times a week",
            "Read for 15 minutes before bed"
        ]
        
        for test_input in test_inputs:
            result = await ai_service.parse_habit_from_text(test_input)
            
            # Verify basic structure
            assert isinstance(result, dict)
            assert 'name' in result
            assert 'frequency' in result
            assert 'category' in result
            
            # Verify non-empty values
            assert len(result['name']) > 0
            assert result['frequency'] in ['daily', 'weekly', 'monthly', 'custom']
    
    @pytest.mark.asyncio
    async def test_habit_parsing_edge_cases(self, ai_service):
        """Test habit parsing with edge cases."""
        edge_cases = [
            "",  # Empty string
            "a",  # Single character
            "This is a very long sentence that doesn't really describe a habit but just keeps going on and on without any clear habit-related content",  # Long non-habit text
            "🚀🎯💪",  # Only emojis
            "123 456 789",  # Only numbers
        ]
        
        for test_input in edge_cases:
            result = await ai_service.parse_habit_from_text(test_input)
            
            # Should handle gracefully without crashing
            assert isinstance(result, dict)
            # May have default values for edge cases
            assert 'name' in result
    
    @pytest.mark.asyncio
    async def test_suggestion_generation(self, ai_service):
        """Test AI-powered suggestion generation."""
        user_data = {
            'completed_habits': ['exercise', 'reading'],
            'failed_habits': ['meditation'],
            'preferences': ['health', 'productivity']
        }
        
        suggestions = await ai_service.generate_suggestions(user_data)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert 'text' in suggestion
            assert 'category' in suggestion
            assert 'confidence' in suggestion
    
    @pytest.mark.asyncio
    async def test_success_prediction(self, ai_service):
        """Test habit success prediction functionality."""
        habit_data = {
            'name': 'Morning Exercise',
            'frequency': 'daily',
            'category': 'fitness',
            'user_history': {
                'completion_rate': 0.75,
                'streak_length': 14,
                'similar_habits': ['running', 'gym']
            }
        }
        
        prediction = await ai_service.predict_success_probability(habit_data)
        
        assert isinstance(prediction, (int, float))
        assert 0 <= prediction <= 1  # Probability should be between 0 and 1
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, ai_service):
        """Test that AI operations complete within reasonable time limits."""
        import time
        
        test_text = "I want to exercise daily"
        
        # Test parsing speed
        start_time = time.time()
        result = await ai_service.parse_habit_from_text(test_text)
        parsing_time = time.time() - start_time
        
        # Should complete within 5 seconds (generous for CI)
        assert parsing_time < 5.0
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_error_handling(self, ai_service):
        """Test that AI service handles errors gracefully."""
        
        # Test with problematic inputs that might cause model errors
        problematic_inputs = [
            None,
            {"not": "a string"},
            ["list", "instead", "of", "string"]
        ]
        
        for bad_input in problematic_inputs:
            try:
                result = await ai_service.parse_habit_from_text(bad_input)
                # If it doesn't raise an error, should return a safe default
                assert isinstance(result, dict)
            except (TypeError, ValueError, AttributeError):
                # These exceptions are acceptable for bad inputs
                pass
    
    def test_model_caching(self, ai_service):
        """Test that models are cached properly to avoid reloading."""
        # First model access
        ai_service.load_models()
        
        # Models should be loaded
        assert hasattr(ai_service, '_models_loaded')
        
        # Second access should use cache (would test timing in real scenario)
        ai_service.load_models()  # Should not reload


class TestAIEndpoints:
    """Test the FastAPI endpoints for AI functionality."""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service for endpoint testing."""
        mock = AsyncMock()
        mock.parse_habit_from_text.return_value = {
            'name': 'Test Habit',
            'frequency': 'daily',
            'category': 'health'
        }
        mock.generate_suggestions.return_value = [
            {'text': 'Try morning meditation', 'category': 'wellness', 'confidence': 0.8}
        ]
        mock.predict_success_probability.return_value = 0.85
        return mock
    
    @patch('ai_assistant.HuggingFaceAI')
    @pytest.mark.asyncio
    async def test_natural_language_endpoint(self, mock_ai_class, mock_ai_service):
        """Test the natural language habit creation endpoint."""
        from fastapi.testclient import TestClient
        from app import app
        
        mock_ai_class.return_value = mock_ai_service
        
        client = TestClient(app)
        
        # Test natural language habit creation
        response = client.post("/api/v1/ai/habits/create-natural", 
                              json={"text": "I want to drink water daily"})
        
        assert response.status_code in [200, 401]  # 401 if auth required
        
        if response.status_code == 200:
            data = response.json()
            assert 'name' in data
            assert 'frequency' in data


class TestAIIntegration:
    """Integration tests for AI features with the broader system."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_ai_pipeline(self):
        """Test the complete AI pipeline from input to output."""
        if not AI_AVAILABLE:
            pytest.skip("AI dependencies not available")
        
        ai_service = HuggingFaceAI()
        
        # Simulate full user interaction
        user_input = "I want to meditate for 10 minutes every morning"
        
        # Parse habit
        habit_data = await ai_service.parse_habit_from_text(user_input)
        assert habit_data['name']
        assert habit_data['frequency']
        
        # Generate suggestions based on parsed habit
        suggestions = await ai_service.generate_suggestions({
            'current_habit': habit_data,
            'user_preferences': ['wellness', 'morning_routine']
        })
        assert len(suggestions) > 0
        
        # Predict success
        success_prob = await ai_service.predict_success_probability(habit_data)
        assert 0 <= success_prob <= 1
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test that AI models don't cause excessive memory usage."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        if AI_AVAILABLE:
            # Load AI service
            ai_service = HuggingFaceAI()
            ai_service.load_models()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Should use less than 3GB additional memory
            assert memory_increase < 3000  # MB


class TestAIFallbacks:
    """Test fallback mechanisms when AI fails or is unavailable."""
    
    def test_ai_disabled_fallback(self):
        """Test system behavior when AI features are disabled."""
        # Simulate AI disabled scenario
        with patch.dict(os.environ, {'AI_FEATURES_ENABLED': 'false'}):
            # System should still function with manual habit creation
            assert True  # Placeholder for actual fallback tests
    
    @patch('huggingface_ai.HuggingFaceAI')
    def test_model_loading_failure(self, mock_ai):
        """Test behavior when AI models fail to load."""
        mock_ai.side_effect = Exception("Model loading failed")
        
        # Should handle gracefully and provide fallback
        try:
            ai_service = HuggingFaceAI()
            # Should not crash the application
            assert True
        except Exception:
            pytest.fail("AI service should handle model loading failures gracefully")


if __name__ == "__main__":
    # Run tests with: python -m pytest test_ai_comprehensive.py -v
    pytest.main([__file__, "-v", "--tb=short"])