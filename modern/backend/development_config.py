"""
Development Environment Configuration and Security Controls

This module provides separate configurations for development and production
environments, implementing security controls appropriate for each context.
"""

import os
from typing import Dict, Any
from config import settings


class DevelopmentSecurityConfig:
    """Security configuration specific to development environments"""
    
    def __init__(self):
        self.is_development = self._detect_development_mode()
        self.dev_overrides = self._get_development_overrides()
    
    def _detect_development_mode(self) -> bool:
        """Detect if running in development mode"""
        # Check various indicators of development environment
        indicators = [
            os.getenv('ENVIRONMENT') == 'development',
            os.getenv('ENV') == 'dev',
            os.getenv('DEBUG') == 'true',
            os.getenv('FLASK_ENV') == 'development',
            os.getenv('NODE_ENV') == 'development',
            'dev' in os.getcwd().lower(),
            os.path.exists('.env.development'),
            not settings.FORCE_HTTPS,  # Likely dev if not forcing HTTPS
            'localhost' in str(settings.FRONTEND_ORIGINS)
        ]
        return any(indicators)
    
    def _get_development_overrides(self) -> Dict[str, Any]:
        """Get security setting overrides for development"""
        if not self.is_development:
            return {}
        
        return {
            # Logging configuration
            'LOG_LEVEL': 'DEBUG',
            'DETAILED_ERRORS': True,
            'LOG_SQL_QUERIES': True,
            
            # CORS configuration (more permissive for dev)
            'CORS_ALLOW_CREDENTIALS': True,
            'CORS_ALLOWED_ORIGINS': [
                'http://localhost:3000',
                'http://localhost:5173',  # Vite default
                'http://127.0.0.1:3000',
                'http://127.0.0.1:5173'
            ],
            
            # Security headers (relaxed for testing)
            'CSP_REPORT_ONLY': True,  # Report violations but don't block
            'HSTS_ENABLE': False,     # No HSTS in development
            
            # Rate limiting (more lenient)
            'RATE_LIMIT_PER_MINUTE': 1000,
            'RATE_LIMIT_BURST': 100,
            
            # Session configuration
            'SESSION_SECURE': False,  # Allow HTTP in development
            'SESSION_HTTPONLY': True,  # Still protect from XSS
            
            # Database security
            'DB_SSL_REQUIRE': False,
            'DB_CONNECTION_POOL_SIZE': 5,
            
            # Development-specific features
            'ENABLE_API_DOCS': True,
            'ENABLE_DEBUG_TOOLBAR': True,
            'ENABLE_HOT_RELOAD': True,
            
            # Testing support
            'ALLOW_TEST_ROUTES': True,
            'MOCK_EXTERNAL_SERVICES': True
        }
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers appropriate for development"""
        if not self.is_development:
            # Use production headers
            return self._get_production_headers()
        
        # Development headers - more permissive for testing
        return {
            "Content-Security-Policy-Report-Only": (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
                "connect-src 'self' ws: wss: http: https:; "
                "font-src 'self' data: https:; "
                "img-src 'self' data: blob: https:; "
                "media-src 'self' blob: https:; "
                "object-src 'none'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "report-uri /api/csp-report"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",  # Less strict for dev tools
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Development-Mode": "true",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    
    def _get_production_headers(self) -> Dict[str, str]:
        """Get strict production security headers"""
        return {
            "Content-Security-Policy": settings.csp_header(),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Strict-Transport-Security": (
                "max-age=31536000; includeSubDomains; preload"
            ),
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), payment=()"
            )
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration for current environment"""
        if self.is_development:
            return {
                "allow_origins": self.dev_overrides['CORS_ALLOWED_ORIGINS'],
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["*"],
                "expose_headers": ["X-Request-ID", "X-API-Version"]
            }
        else:
            # Production CORS - more restrictive
            return {
                "allow_origins": settings.FRONTEND_ORIGINS,
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE"],
                "allow_headers": [
                    "Authorization",
                    "Content-Type",
                    "X-CSRF-Token",
                    "X-API-Key"
                ],
                "expose_headers": ["X-Request-ID"]
            }
    
    def get_rate_limit_config(self) -> Dict[str, int]:
        """Get rate limiting configuration"""
        if self.is_development:
            return {
                "requests_per_minute": self.dev_overrides[
                    'RATE_LIMIT_PER_MINUTE'],
                "burst_limit": self.dev_overrides['RATE_LIMIT_BURST']
            }
        else:
            return {
                "requests_per_minute": 60,
                "burst_limit": 20
            }
    
    def should_log_sql(self) -> bool:
        """Whether to log SQL queries"""
        return (self.is_development and
                self.dev_overrides.get('LOG_SQL_QUERIES', False))
    
    def should_enable_debug_routes(self) -> bool:
        """Whether to enable debug/test routes"""
        return (self.is_development and
                self.dev_overrides.get('ALLOW_TEST_ROUTES', False))
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get session configuration for current environment"""
        if self.is_development:
            return {
                "secure": self.dev_overrides['SESSION_SECURE'],
                "httponly": self.dev_overrides['SESSION_HTTPONLY'],
                "samesite": "lax",
                "max_age": 3600 * 24  # 24 hours for development
            }
        else:
            return {
                "secure": True,
                "httponly": True,
                "samesite": "strict",
                "max_age": 3600 * 8  # 8 hours for production
            }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        if self.is_development:
            return {
                "level": "DEBUG",
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(filename)s:%(lineno)d - %(message)s"
                ),
                "include_trace": True,
                "log_sql": True,
                "log_requests": True
            }
        else:
            return {
                "level": "INFO",
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                "include_trace": False,
                "log_sql": False,
                "log_requests": False
            }
    
    def validate_development_security(self) -> Dict[str, Any]:
        """Validate that development environment is properly secured"""
        warnings = []
        recommendations = []
        
        if self.is_development:
            # Check for potential security issues in development
            if os.getenv('SECRET_KEY') == 'dev-secret-key':
                warnings.append("Using default development secret key")
                recommendations.append(
                    "Set unique SECRET_KEY even in development")
            
            db_url = os.getenv('DATABASE_URL', '')
            if not db_url.startswith('sqlite'):
                if 'localhost' not in db_url:
                    warnings.append("Database not on localhost in development")
                    recommendations.append(
                        "Use local database for development")
            
            redis_url = os.getenv('REDIS_URL', '')
            if redis_url and 'localhost' not in redis_url:
                warnings.append("Redis not on localhost in development")
                recommendations.append(
                    "Use local Redis instance for development")
            
            # Check for production data in development
            if 'prod' in os.getcwd().lower():
                warnings.append(
                    "Development mode detected in production-like path")
                recommendations.append(
                    "Ensure separate development environment")
        
        return {
            "is_development": self.is_development,
            "warnings": warnings,
            "recommendations": recommendations,
            "config_overrides": len(self.dev_overrides),
            "environment_secure": len(warnings) == 0
        }


# Global instance
dev_config = DevelopmentSecurityConfig()


def get_environment_config() -> DevelopmentSecurityConfig:
    """Get the development configuration instance"""
    return dev_config


def is_development_mode() -> bool:
    """Quick check if running in development mode"""
    return dev_config.is_development


def get_security_config_for_environment() -> Dict[str, Any]:
    """Get complete security configuration for current environment"""
    env_name = ("development" if dev_config.is_development
                else "production")
    
    config = {
        "environment": env_name,
        "security_headers": dev_config.get_security_headers(),
        "cors_config": dev_config.get_cors_config(),
        "rate_limit_config": dev_config.get_rate_limit_config(),
        "session_config": dev_config.get_session_config(),
        "logging_config": dev_config.get_logging_config(),
        "validation": dev_config.validate_development_security()
    }
    
    return config
