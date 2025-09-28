"""
Secure test data utilities - no hardcoded credentials
"""
import secrets
import string
from typing import Dict, Any
import bcrypt
from datetime import datetime, timedelta


class SecureTestDataGenerator:
    """Generate secure test data dynamically"""
    
    def __init__(self):
        self.session_data = {}  # Store data for test session
    
    def generate_secure_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_email(self, domain: str = "test.example.com") -> str:
        """Generate a unique test email"""
        username = secrets.token_hex(8)
        return f"test-{username}@{domain}"
    
    def generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret for testing"""
        return secrets.token_urlsafe(64)
    
    def generate_user_data(self, role: str = "user") -> Dict[str, Any]:
        """Generate secure test user data"""
        password = self.generate_secure_password()
        email = self.generate_email()
        
        user_data = {
            "email": email,
            "password": password,
            "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "display_name": f"Test User {secrets.token_hex(4)}",
            "role": role,
            "created_at": datetime.utcnow(),
        }
        
        # Store for test session
        self.session_data[f"user_{email}"] = user_data
        return user_data
    
    def generate_habit_data(self, user_id: int) -> Dict[str, Any]:
        """Generate test habit data"""
        habits = [
            "Read for 30 minutes",
            "Exercise for 45 minutes", 
            "Meditate for 10 minutes",
            "Write in journal",
            "Practice coding",
        ]
        
        return {
            "title": f"{secrets.choice(habits)} - {secrets.token_hex(2)}",
            "description": f"Test habit description {secrets.token_hex(4)}",
            "user_id": user_id,
            "category": secrets.choice(["health", "productivity", "learning", "mindfulness"]),
            "difficulty": secrets.randbelow(5) + 1,
            "created_at": datetime.utcnow(),
        }
    
    def generate_project_data(self, user_id: int) -> Dict[str, Any]:
        """Generate test project data"""
        projects = [
            "Build a personal website",
            "Learn a new programming language",
            "Complete online course",
            "Write a blog post",
            "Create a mobile app",
        ]
        
        return {
            "title": f"{secrets.choice(projects)} - {secrets.token_hex(2)}",
            "description": f"Test project description {secrets.token_hex(6)}",
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "due_date": datetime.utcnow() + timedelta(days=secrets.randbelow(90) + 1),
        }
    
    def generate_api_token(self, user_id: int) -> Dict[str, Any]:
        """Generate test API token"""
        return {
            "name": f"Test Token {secrets.token_hex(3)}",
            "token": secrets.token_urlsafe(32),
            "user_id": user_id,
            "permissions": ["read:habits", "read:projects"],
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "created_at": datetime.utcnow(),
        }
    
    def cleanup_session_data(self):
        """Clear all session test data"""
        self.session_data.clear()
    
    def get_test_database_url(self) -> str:
        """Generate isolated test database URL"""
        db_name = f"test_liferpg_{secrets.token_hex(8)}"
        return f"sqlite:///./{db_name}.db"


# Global test data generator
test_data_generator = SecureTestDataGenerator()


def create_test_environment():
    """Set up secure test environment variables"""
    import os
    
    # Only set if not already configured
    test_env = {
        "LIFERPG_JWT_SECRET": test_data_generator.generate_jwt_secret(),
        "DATABASE_URL": test_data_generator.get_test_database_url(),
        "ENVIRONMENT": "test",
        "CSRF_ENABLE": "false",  # Disable CSRF for API tests
        "RATE_LIMIT_PER_MINUTE": "1000",  # Higher limit for tests
        "ENCRYPTION_KEY": secrets.token_urlsafe(32),
    }
    
    for key, value in test_env.items():
        if key not in os.environ:
            os.environ[key] = value
    
    return test_env


def cleanup_test_environment():
    """Clean up test environment"""
    import os
    
    # Remove test database files
    test_files = [f for f in os.listdir('.') if f.startswith('test_liferpg_') and f.endswith('.db')]
    for file in test_files:
        try:
            os.remove(file)
        except OSError:
            pass
    
    # Clear test data
    test_data_generator.cleanup_session_data()