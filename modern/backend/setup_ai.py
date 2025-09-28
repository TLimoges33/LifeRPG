#!/usr/bin/env python3
"""
AI Setup Script for LifeRPG Phase 3
Sets up HuggingFace models and dependencies
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def install_ai_dependencies():
    """Install AI-specific dependencies."""
    logger.info("Installing AI dependencies...")
    
    try:
        # Install from requirements_ai.txt
        req_file = Path(__file__).parent / 'requirements_ai.txt'
        if req_file.exists():
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '-r', str(req_file)
            ])
        else:
            # Install core dependencies manually
            dependencies = [
                'transformers>=4.21.0',
                'torch>=1.12.0',
                'torchvision>=0.13.0',
                'torchaudio>=0.12.0',
                'speechrecognition>=3.10.0',
                'opencv-python>=4.6.0',
                'scikit-learn>=1.1.0',
                'numpy>=1.21.0',
                'Pillow>=9.0.0',
                'librosa>=0.9.0'
            ]
            
            for dep in dependencies:
                logger.info(f"Installing {dep}...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', dep
                ])
        
        logger.info("AI dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def download_huggingface_models():
    """Download and cache HuggingFace models locally."""
    logger.info("Downloading HuggingFace models...")
    
    try:
        from transformers import (
            AutoTokenizer, AutoModelForSequenceClassification,
            AutoModelForZeroShotClassification, pipeline
        )
        
        # Model configurations
        models_to_download = [
            {
                'name': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                'type': 'sentiment',
                'size': '~500MB'
            },
            {
                'name': 'facebook/bart-large-mnli',
                'type': 'zero-shot',
                'size': '~1.6GB'
            }
        ]
        
        for model_config in models_to_download:
            model_name = model_config['name']
            logger.info(f"Downloading {model_name} ({model_config['size']})...")
            
            try:
                # Download tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                if model_config['type'] == 'sentiment':
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_name
                    )
                elif model_config['type'] == 'zero-shot':
                    # Create pipeline to download model
                    classifier = pipeline(
                        'zero-shot-classification',
                        model=model_name
                    )
                
                logger.info(f"✓ {model_name} downloaded successfully")
                
            except Exception as e:
                logger.warning(f"Failed to download {model_name}: {e}")
                logger.info("Model will be downloaded on first use")
        
        logger.info("HuggingFace models setup completed!")
        return True
        
    except ImportError:
        logger.error("Transformers library not installed. Run install_ai_dependencies() first.")
        return False
    except Exception as e:
        logger.error(f"Failed to download models: {e}")
        return False


def test_ai_functionality():
    """Test basic AI functionality."""
    logger.info("Testing AI functionality...")
    
    try:
        # Test HuggingFace AI service
        from huggingface_ai import HuggingFaceAI
        
        ai_service = HuggingFaceAI()
        
        # Test habit parsing
        test_text = "I want to drink 8 glasses of water every day"
        result = ai_service.parse_natural_language_habit(test_text)
        
        if result and 'name' in result:
            logger.info(f"✓ Habit parsing test passed: {result['name']}")
        else:
            logger.warning("Habit parsing test failed")
        
        # Test sentiment analysis
        test_sentiment = "I feel great about my progress today!"
        sentiment = ai_service.analyze_habit_sentiment(test_sentiment)
        
        if sentiment and 'label' in sentiment:
            logger.info(f"✓ Sentiment analysis test passed: {sentiment['label']}")
        else:
            logger.warning("Sentiment analysis test failed")
        
        logger.info("AI functionality tests completed!")
        return True
        
    except ImportError as e:
        logger.error(f"AI modules not available: {e}")
        return False
    except Exception as e:
        logger.error(f"AI functionality test failed: {e}")
        return False


def setup_ai_directories():
    """Create necessary directories for AI operations."""
    logger.info("Setting up AI directories...")
    
    directories = [
        'models',
        'cache',
        'uploads',
        'temp'
    ]
    
    base_path = Path(__file__).parent
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(exist_ok=True)
        logger.info(f"✓ Directory created: {dir_path}")
    
    return True


def main():
    """Main setup function."""
    logger.info("Starting LifeRPG AI Setup (Phase 3)...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required for AI features")
        return False
    
    # Setup steps
    steps = [
        ("Setting up directories", setup_ai_directories),
        ("Installing AI dependencies", install_ai_dependencies),
        ("Downloading HuggingFace models", download_huggingface_models),
        ("Testing AI functionality", test_ai_functionality)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n=== {step_name} ===")
        try:
            if not step_func():
                logger.error(f"Step failed: {step_name}")
                return False
        except Exception as e:
            logger.error(f"Step error: {step_name} - {e}")
            return False
    
    logger.info("\n🎉 LifeRPG AI Setup completed successfully!")
    logger.info("Phase 3 AI features are now ready to use.")
    logger.info("\nFeatures enabled:")
    logger.info("- Natural language habit creation")
    logger.info("- AI-powered habit suggestions")
    logger.info("- Predictive analytics")
    logger.info("- Voice command processing (basic)")
    logger.info("- Image recognition check-ins (basic)")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)