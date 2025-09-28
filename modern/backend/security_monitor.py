"""
Security monitoring and alerting system
"""
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import hashlib


class SecurityEventType(Enum):
    """Security event types for monitoring"""
    LOGIN_FAILURE = "login_failure"
    LOGIN_SUCCESS = "login_success"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_2FA = "invalid_2fa"
    ACCOUNT_LOCKOUT = "account_lockout"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_VIOLATION = "csrf_violation"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    ANOMALOUS_LOGIN_LOCATION = "anomalous_login_location"
    PASSWORD_BRUTE_FORCE = "password_brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXPORT_LARGE = "data_export_large"
    ADMIN_ACTION = "admin_action"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    user_id: str = None
    ip_address: str = None
    user_agent: str = None
    request_path: str = None
    timestamp: datetime = None
    details: Dict[str, Any] = None
    severity: str = "medium"  # low, medium, high, critical
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


class SecurityMonitor:
    """Security monitoring and alerting system"""
    
    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.logger = self._setup_security_logger()
        self.alert_thresholds = {
            SecurityEventType.LOGIN_FAILURE: {"count": 5, "window_minutes": 5},
            SecurityEventType.RATE_LIMIT_EXCEEDED: {"count": 10, "window_minutes": 1},
            SecurityEventType.INVALID_2FA: {"count": 3, "window_minutes": 5},
            SecurityEventType.UNAUTHORIZED_ACCESS: {"count": 1, "window_minutes": 1},
        }
        self.blocked_ips: Dict[str, datetime] = {}
    
    def _setup_security_logger(self):
        """Set up dedicated security event logger"""
        logger = logging.getLogger("security")
        logger.setLevel(logging.INFO)
        
        # Create security log handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_event(self, event: SecurityEvent):
        """Log a security event"""
        self.events.append(event)
        
        # Log to security logger
        log_data = {
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "ip_address": self._hash_ip(event.ip_address) if event.ip_address else None,
            "user_agent_hash": self._hash_user_agent(event.user_agent) if event.user_agent else None,
            "request_path": event.request_path,
            "timestamp": event.timestamp.isoformat(),
            "severity": event.severity,
            "details": event.details,
        }
        
        self.logger.info(json.dumps(log_data))
        
        # Check for alert conditions
        self._check_alert_conditions(event)
        
        # Cleanup old events (keep last 1000)
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
    
    def _hash_ip(self, ip: str) -> str:
        """Hash IP for privacy while maintaining uniqueness"""
        return hashlib.sha256(f"ip_{ip}".encode()).hexdigest()[:16]
    
    def _hash_user_agent(self, user_agent: str) -> str:
        """Hash user agent for privacy"""
        return hashlib.sha256(f"ua_{user_agent}".encode()).hexdigest()[:16]
    
    def _check_alert_conditions(self, event: SecurityEvent):
        """Check if event triggers an alert"""
        event_type = event.event_type
        
        if event_type not in self.alert_thresholds:
            return
        
        threshold = self.alert_thresholds[event_type]
        window_start = datetime.utcnow() - timedelta(minutes=threshold["window_minutes"])
        
        # Count recent events of this type from same IP
        recent_events = [
            e for e in self.events
            if (e.event_type == event_type and 
                e.ip_address == event.ip_address and 
                e.timestamp >= window_start)
        ]
        
        if len(recent_events) >= threshold["count"]:
            self._trigger_alert(event, recent_events)
    
    def _trigger_alert(self, event: SecurityEvent, recent_events: List[SecurityEvent]):
        """Trigger security alert"""
        alert_data = {
            "alert_type": "security_threshold_exceeded",
            "event_type": event.event_type.value,
            "ip_address": self._hash_ip(event.ip_address) if event.ip_address else None,
            "event_count": len(recent_events),
            "time_window": self.alert_thresholds[event.event_type]["window_minutes"],
            "timestamp": datetime.utcnow().isoformat(),
            "recommended_action": self._get_recommended_action(event.event_type),
        }
        
        self.logger.warning(f"SECURITY ALERT: {json.dumps(alert_data)}")
        
        # Auto-block IP for certain event types
        if event.event_type in [SecurityEventType.PASSWORD_BRUTE_FORCE, 
                                SecurityEventType.RATE_LIMIT_EXCEEDED]:
            self._block_ip(event.ip_address)
    
    def _get_recommended_action(self, event_type: SecurityEventType) -> str:
        """Get recommended action for event type"""
        actions = {
            SecurityEventType.LOGIN_FAILURE: "Consider IP blocking or account lockout",
            SecurityEventType.RATE_LIMIT_EXCEEDED: "IP temporarily blocked",
            SecurityEventType.INVALID_2FA: "Monitor for account compromise",
            SecurityEventType.UNAUTHORIZED_ACCESS: "Investigate immediately",
            SecurityEventType.PASSWORD_BRUTE_FORCE: "IP blocked, notify user",
        }
        return actions.get(event_type, "Monitor and investigate")
    
    def _block_ip(self, ip_address: str, duration_minutes: int = 30):
        """Block IP address temporarily"""
        if ip_address:
            block_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
            self.blocked_ips[ip_address] = block_until
            
            self.logger.warning(f"IP {self._hash_ip(ip_address)} blocked until {block_until}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is currently blocked"""
        if not ip_address or ip_address not in self.blocked_ips:
            return False
        
        block_until = self.blocked_ips[ip_address]
        if datetime.utcnow() > block_until:
            # Block expired, remove it
            del self.blocked_ips[ip_address]
            return False
        
        return True
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for dashboard"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_events = [e for e in self.events if e.timestamp >= last_hour]
        daily_events = [e for e in self.events if e.timestamp >= last_day]
        
        metrics = {
            "events_last_hour": len(recent_events),
            "events_last_24h": len(daily_events),
            "blocked_ips_count": len(self.blocked_ips),
            "top_event_types_hour": self._get_top_event_types(recent_events),
            "top_event_types_day": self._get_top_event_types(daily_events),
            "critical_events_hour": len([e for e in recent_events if e.severity == "critical"]),
        }
        
        return metrics
    
    def _get_top_event_types(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Get top event types by count"""
        event_counts = {}
        for event in events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Return top 5
        return dict(sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:5])


# Global security monitor instance
security_monitor = SecurityMonitor()


# Helper functions for easy integration
def log_login_failure(user_id: str, ip_address: str, user_agent: str = None):
    """Log login failure event"""
    event = SecurityEvent(
        event_type=SecurityEventType.LOGIN_FAILURE,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        severity="medium"
    )
    security_monitor.log_event(event)


def log_unauthorized_access(user_id: str, ip_address: str, request_path: str, user_agent: str = None):
    """Log unauthorized access attempt"""
    event = SecurityEvent(
        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        severity="high"
    )
    security_monitor.log_event(event)


def log_rate_limit_exceeded(ip_address: str, request_path: str, user_agent: str = None):
    """Log rate limit exceeded event"""
    event = SecurityEvent(
        event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        severity="medium"
    )
    security_monitor.log_event(event)


def check_ip_blocked(ip_address: str) -> bool:
    """Check if IP is blocked"""
    return security_monitor.is_ip_blocked(ip_address)