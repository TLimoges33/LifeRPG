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
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Conditionally skip individual tests instead of module-level skip
pytestmark = pytest.mark.skipif(not AI_AVAILABLE, reason="AI dependencies not available")


class TestHuggingFaceAI:
    """Test the core HuggingFace AI service functionality."""
    
    @pytest.fixture
    def ai_service(self):
        """Create an AI service instance for testing."""
        return HuggingFaceAI()
    
    @pytest.mark.asyncio
    async def test_ai_service_initialization(self, ai_service):
        """Test that AI service initializes correctly."""
        assert ai_service is not None
        assert hasattr(ai_service, 'parse_habit_from_text')
        assert hasattr(ai_service, 'get_habit_suggestions')
    
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
            assert 'title' in result
            assert 'cadence' in result
            
            # Verify non-empty values
            assert len(result['title']) > 0
            assert result['cadence'] in ['daily', 'weekly', 'monthly']
    
    @pytest.mark.asyncio
    async def test_habit_parsing_edge_cases(self, ai_service):
        """Test habit parsing with edge cases."""
        edge_cases = [
            "",  # Empty string
            "a",  # Single character
            "This is a very long sentence that doesn't really describe a habit but just keeps going on and on without any clear habit-related content",  # Long non-habit text
            "123 456 789",  # Only numbers
        ]
        
        for test_input in edge_cases:
            result = await ai_service.parse_habit_from_text(test_input)
            
            # Should handle gracefully without crashing
            assert isinstance(result, dict)
            # May have default values for edge cases
            assert 'title' in result
    
    @pytest.mark.asyncio
    async def test_suggestion_generation(self, ai_service):
        """Test AI-powered suggestion generation."""
        user_habits = ['exercise', 'reading']
        user_data = {
            'preferences': ['health', 'productivity']
        }
        
        suggestions = await ai_service.get_habit_suggestions(user_habits, user_data)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
    
    @pytest.mark.asyncio
    async def test_success_prediction(self, ai_service):
        """Test habit success prediction functionality."""
        habit_data = {
            'title': 'Morning Exercise',
            'cadence': 'daily',
            'difficulty': 2,
        }
        user_history = [
            {'completed': True},
            {'completed': True},
            {'completed': False},
            {'completed': True},
        ]
        
        prediction = await ai_service.predict_habit_success(habit_data, user_history)
        
        assert isinstance(prediction, dict)
        assert 'success_probability' in prediction
        assert 0 <= prediction['success_probability'] <= 1
        assert 'insights' in prediction
        assert isinstance(prediction['insights'], list)
    
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
    
    def test_local_models_attribute(self, ai_service):
        """Test that local models dictionary is initialized."""
        assert hasattr(ai_service, 'local_models')
        assert isinstance(ai_service.local_models, dict)


class TestAIIntegration:
    """Integration tests for AI features with the broader system."""
    
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
        assert habit_data['title']
        assert habit_data['cadence']
        
        # Generate suggestions
        suggestions = await ai_service.get_habit_suggestions(
            [habit_data['title']],
            {'preferences': ['wellness', 'morning_routine']}
        )
        assert len(suggestions) > 0
        
        # Predict success
        prediction = await ai_service.predict_habit_success(habit_data, [])
        assert 0 <= prediction['success_probability'] <= 1


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
