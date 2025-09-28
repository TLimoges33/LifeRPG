"""
Secure logging utilities that sanitize sensitive data
"""
import logging
import re
import json
from typing import Any, Dict, Union
from datetime import datetime


class SecureLogger:
    """Logger that automatically sanitizes sensitive data"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # Patterns for sensitive data detection
        self.sensitive_patterns = {
            'password': [
                r'password["\']?\s*[:=]\s*["\']?([^"\';\s]+)',
                r'pwd["\']?\s*[:=]\s*["\']?([^"\';\s]+)',
                r'passwd["\']?\s*[:=]\s*["\']?([^"\';\s]+)',
            ],
            'token': [
                r'token["\']?\s*[:=]\s*["\']?([A-Za-z0-9+/=]{20,})',
                r'jwt["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)',
                r'bearer\s+([A-Za-z0-9+/=]{20,})',
            ],
            'api_key': [
                r'api[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{16,})',
                r'secret[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{16,})',
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            ],
            'phone': [
                r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
            ],
            'ssn': [
                r'(\d{3}-?\d{2}-?\d{4})',
            ],
            'credit_card': [
                r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})',
            ],
            'private_key': [
                r'(-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----)',
                r'(-----BEGIN RSA PRIVATE KEY-----.*?-----END RSA PRIVATE KEY-----)',
            ]
        }
    
    def sanitize_message(self, message: str) -> str:
        """Sanitize sensitive data from log message"""
        sanitized = message
        
        for data_type, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                # Replace sensitive data with placeholder
                sanitized = re.sub(
                    pattern, 
                    lambda m: f'[REDACTED_{data_type.upper()}]',
                    sanitized,
                    flags=re.IGNORECASE | re.DOTALL
                )
        
        return sanitized
    
    def sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data structures"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Sanitize key names that might contain sensitive info
                safe_key = self.sanitize_message(str(key))
                # Recursively sanitize values
                safe_value = self.sanitize_data(value)
                sanitized[safe_key] = safe_value
            return sanitized
        
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        
        elif isinstance(data, str):
            return self.sanitize_message(data)
        
        else:
            return data
    
    def _log_with_sanitization(self, level: int, message: str, *args, **kwargs):
        """Internal method to log with sanitization"""
        # Sanitize the message
        safe_message = self.sanitize_message(message)
        
        # Sanitize args
        safe_args = tuple(self.sanitize_data(arg) for arg in args)
        
        # Sanitize kwargs
        safe_kwargs = self.sanitize_data(kwargs)
        
        # Log with sanitized data
        self.logger.log(level, safe_message, *safe_args, **safe_kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Debug level logging with sanitization"""
        self._log_with_sanitization(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Info level logging with sanitization"""
        self._log_with_sanitization(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Warning level logging with sanitization"""
        self._log_with_sanitization(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Error level logging with sanitization"""
        self._log_with_sanitization(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Critical level logging with sanitization"""
        self._log_with_sanitization(logging.CRITICAL, message, *args, **kwargs)
    
    def log_request(self, request_data: Dict[str, Any]):
        """Log HTTP request with sanitization"""
        safe_data = self.sanitize_data({
            'method': request_data.get('method'),
            'path': request_data.get('path'),
            'user_agent': request_data.get('user_agent'),
            'ip_address_hash': request_data.get('ip_hash'),
            'timestamp': datetime.utcnow().isoformat(),
            'headers': {k: v for k, v in request_data.get('headers', {}).items() 
                       if k.lower() not in ['authorization', 'cookie']},
        })
        
        self.info(f"HTTP Request: {json.dumps(safe_data)}")
    
    def log_auth_event(self, event_data: Dict[str, Any]):
        """Log authentication events with sanitization"""
        safe_data = self.sanitize_data({
            'event_type': event_data.get('event_type'),
            'user_id_hash': event_data.get('user_id_hash'),
            'ip_address_hash': event_data.get('ip_hash'),
            'success': event_data.get('success'),
            'timestamp': datetime.utcnow().isoformat(),
            'details': event_data.get('details', {}),
        })
        
        level = logging.INFO if event_data.get('success') else logging.WARNING
        self._log_with_sanitization(level, f"Auth Event: {json.dumps(safe_data)}")


class StructuredLogFormatter(logging.Formatter):
    """Structured logging formatter for security events"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        return json.dumps(log_entry)


# Global secure loggers for different components
auth_logger = SecureLogger('liferpg.auth')
api_logger = SecureLogger('liferpg.api')
security_logger = SecureLogger('liferpg.security')
plugin_logger = SecureLogger('liferpg.plugins')


def setup_secure_logging():
    """Setup secure logging configuration"""
    # Create structured formatter
    formatter = StructuredLogFormatter()
    
    # Setup handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger('liferpg')
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    # Prevent duplicate logs
    root_logger.propagate = False