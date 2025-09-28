"""
Advanced rate limiting with user-based and IP-based controls
Provides comprehensive protection against abuse with flexible configuration
"""

import time
import asyncio
import json
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Types of rate limits"""
    USER_BASED = "user"
    IP_BASED = "ip" 
    GLOBAL = "global"
    ENDPOINT_SPECIFIC = "endpoint"
    SLIDING_WINDOW = "sliding"
    FIXED_WINDOW = "fixed"


class RateLimitAction(Enum):
    """Actions to take when rate limit is exceeded"""
    BLOCK = "block"
    THROTTLE = "throttle"
    WARNING = "warning"
    LOG_ONLY = "log"


@dataclass
class RateLimitRule:
    """Configuration for a rate limit rule"""
    max_requests: int
    window_seconds: int
    limit_type: RateLimitType
    action: RateLimitAction = RateLimitAction.BLOCK
    burst_allowance: int = 0
    throttle_delay: float = 1.0
    endpoints: List[str] = None
    user_tiers: List[str] = None  # premium, basic, free
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = ["*"]  # Apply to all endpoints
        if self.user_tiers is None:
            self.user_tiers = ["*"]  # Apply to all user tiers


@dataclass 
class RateLimitStatus:
    """Current rate limit status for a key"""
    requests_made: int
    requests_remaining: int
    reset_time: datetime
    is_limited: bool
    action: RateLimitAction
    retry_after: Optional[int] = None


class AdvancedRateLimiter:
    """
    Advanced rate limiting with multiple strategies and storage backends
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.local_cache = defaultdict(lambda: defaultdict(deque))
        self.rules: Dict[str, RateLimitRule] = {}
        self.user_tiers = {}  # user_id -> tier mapping
        
        # Default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default rate limiting rules"""
        
        # General API rate limits by user tier
        self.add_rule("user_basic", RateLimitRule(
            max_requests=1000,
            window_seconds=3600,  # 1 hour
            limit_type=RateLimitType.USER_BASED,
            user_tiers=["basic", "free"]
        ))
        
        self.add_rule("user_premium", RateLimitRule(
            max_requests=5000,
            window_seconds=3600,  # 1 hour
            limit_type=RateLimitType.USER_BASED,
            user_tiers=["premium", "pro"]
        ))
        
        # IP-based limits for anonymous users
        self.add_rule("ip_anonymous", RateLimitRule(
            max_requests=100,
            window_seconds=3600,  # 1 hour
            limit_type=RateLimitType.IP_BASED
        ))
        
        # Strict limits for authentication endpoints
        self.add_rule("auth_endpoints", RateLimitRule(
            max_requests=5,
            window_seconds=300,  # 5 minutes
            limit_type=RateLimitType.USER_BASED,
            endpoints=["/auth/login", "/auth/register", "/auth/reset-password"],
            action=RateLimitAction.BLOCK
        ))
        
        # More lenient limits for read operations
        self.add_rule("read_operations", RateLimitRule(
            max_requests=500,
            window_seconds=300,  # 5 minutes
            limit_type=RateLimitType.USER_BASED,
            endpoints=["/habits", "/analytics", "/profile"],
            burst_allowance=50
        ))
        
        # Strict limits for write operations
        self.add_rule("write_operations", RateLimitRule(
            max_requests=100,
            window_seconds=300,  # 5 minutes
            limit_type=RateLimitType.USER_BASED,
            endpoints=["/habits/create", "/habits/*/complete", "/habits/*/update"],
            action=RateLimitAction.THROTTLE,
            throttle_delay=2.0
        ))
        
        # Global rate limits for server protection
        self.add_rule("global_protection", RateLimitRule(
            max_requests=10000,
            window_seconds=60,  # 1 minute
            limit_type=RateLimitType.GLOBAL
        ))
    
    def add_rule(self, rule_id: str, rule: RateLimitRule):
        """Add a new rate limiting rule"""
        self.rules[rule_id] = rule
        logger.info(f"Added rate limit rule: {rule_id}")
    
    def set_user_tier(self, user_id: str, tier: str):
        """Set the tier for a user (basic, premium, pro, etc.)"""
        self.user_tiers[user_id] = tier
    
    def get_user_tier(self, user_id: str) -> str:
        """Get the tier for a user, default to 'basic'"""
        return self.user_tiers.get(user_id, "basic")
    
    async def check_rate_limit(self, 
                              request: Request,
                              user_id: Optional[str] = None,
                              endpoint: Optional[str] = None) -> RateLimitStatus:
        """
        Check if a request should be rate limited
        Returns RateLimitStatus with current status
        """
        
        # Determine applicable rules
        applicable_rules = self._get_applicable_rules(
            user_id=user_id,
            endpoint=endpoint,
            ip=self._get_client_ip(request)
        )
        
        # Check each applicable rule
        most_restrictive_status = None
        
        for rule_id, rule in applicable_rules:
            key = self._generate_key(rule, user_id, self._get_client_ip(request))
            status = await self._check_rule(rule, key)
            
            # Track most restrictive limit
            if (most_restrictive_status is None or 
                status.is_limited or 
                status.requests_remaining < most_restrictive_status.requests_remaining):
                most_restrictive_status = status
        
        return most_restrictive_status or RateLimitStatus(
            requests_made=0,
            requests_remaining=float('inf'),
            reset_time=datetime.now() + timedelta(hours=1),
            is_limited=False,
            action=RateLimitAction.LOG_ONLY
        )
    
    async def record_request(self, 
                            request: Request,
                            user_id: Optional[str] = None,
                            endpoint: Optional[str] = None):
        """Record a request for rate limiting purposes"""
        
        applicable_rules = self._get_applicable_rules(
            user_id=user_id,
            endpoint=endpoint,
            ip=self._get_client_ip(request)
        )
        
        # Record request for each applicable rule
        for rule_id, rule in applicable_rules:
            key = self._generate_key(rule, user_id, self._get_client_ip(request))
            await self._record_request_for_rule(rule, key)
    
    def _get_applicable_rules(self, 
                             user_id: Optional[str],
                             endpoint: Optional[str],
                             ip: str) -> List[tuple]:
        """Get rules that apply to this request"""
        
        applicable_rules = []
        user_tier = self.get_user_tier(user_id) if user_id else "anonymous"
        
        for rule_id, rule in self.rules.items():
            # Check if rule applies to this user tier
            if "*" not in rule.user_tiers and user_tier not in rule.user_tiers:
                continue
            
            # Check if rule applies to this endpoint
            if endpoint and "*" not in rule.endpoints:
                endpoint_matches = False
                for pattern in rule.endpoints:
                    if self._endpoint_matches(endpoint, pattern):
                        endpoint_matches = True
                        break
                if not endpoint_matches:
                    continue
            
            # Check if we have required identifiers for the rule type
            if rule.limit_type == RateLimitType.USER_BASED and not user_id:
                continue
            
            applicable_rules.append((rule_id, rule))
        
        return applicable_rules
    
    def _endpoint_matches(self, endpoint: str, pattern: str) -> bool:
        """Check if an endpoint matches a pattern (supports wildcards)"""
        if pattern == "*":
            return True
        
        # Simple wildcard matching
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return endpoint.startswith(prefix) and endpoint.endswith(suffix)
        
        return endpoint == pattern
    
    def _generate_key(self, 
                     rule: RateLimitRule,
                     user_id: Optional[str],
                     ip: str) -> str:
        """Generate a cache key for the rate limit"""
        
        if rule.limit_type == RateLimitType.USER_BASED:
            return f"rate_limit:user:{user_id}:{rule.window_seconds}"
        elif rule.limit_type == RateLimitType.IP_BASED:
            return f"rate_limit:ip:{ip}:{rule.window_seconds}"
        elif rule.limit_type == RateLimitType.GLOBAL:
            return f"rate_limit:global:{rule.window_seconds}"
        else:
            return f"rate_limit:custom:{user_id or ip}:{rule.window_seconds}"
    
    async def _check_rule(self, rule: RateLimitRule, key: str) -> RateLimitStatus:
        """Check rate limit for a specific rule"""
        
        now = time.time()
        window_start = now - rule.window_seconds
        
        if self.redis:
            return await self._check_rule_redis(rule, key, now, window_start)
        else:
            return await self._check_rule_memory(rule, key, now, window_start)
    
    async def _check_rule_redis(self, 
                               rule: RateLimitRule,
                               key: str,
                               now: float,
                               window_start: float) -> RateLimitStatus:
        """Check rate limit using Redis storage"""
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current entries
        pipe.zcard(key)
        
        # Set expiration
        pipe.expire(key, rule.window_seconds)
        
        results = await pipe.execute()
        current_count = results[1]
        
        requests_remaining = max(0, rule.max_requests - current_count)
        is_limited = current_count >= rule.max_requests
        
        return RateLimitStatus(
            requests_made=current_count,
            requests_remaining=requests_remaining,
            reset_time=datetime.fromtimestamp(now + rule.window_seconds),
            is_limited=is_limited,
            action=rule.action,
            retry_after=rule.window_seconds if is_limited else None
        )
    
    async def _check_rule_memory(self, 
                                rule: RateLimitRule,
                                key: str,
                                now: float,
                                window_start: float) -> RateLimitStatus:
        """Check rate limit using in-memory storage"""
        
        requests = self.local_cache[key]['requests']
        
        # Remove old requests
        while requests and requests[0] < window_start:
            requests.popleft()
        
        current_count = len(requests)
        requests_remaining = max(0, rule.max_requests - current_count)
        is_limited = current_count >= rule.max_requests
        
        return RateLimitStatus(
            requests_made=current_count,
            requests_remaining=requests_remaining,
            reset_time=datetime.fromtimestamp(now + rule.window_seconds),
            is_limited=is_limited,
            action=rule.action,
            retry_after=rule.window_seconds if is_limited else None
        )
    
    async def _record_request_for_rule(self, rule: RateLimitRule, key: str):
        """Record a request for a specific rule"""
        
        now = time.time()
        
        if self.redis:
            await self._record_request_redis(key, now, rule.window_seconds)
        else:
            await self._record_request_memory(key, now)
    
    async def _record_request_redis(self, key: str, timestamp: float, window_seconds: int):
        """Record a request using Redis"""
        
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(timestamp): timestamp})
        pipe.expire(key, window_seconds)
        await pipe.execute()
    
    async def _record_request_memory(self, key: str, timestamp: float):
        """Record a request using in-memory storage"""
        
        requests = self.local_cache[key]['requests']
        requests.append(timestamp)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        
        # Check for forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def get_rate_limit_info(self, 
                                 request: Request,
                                 user_id: Optional[str] = None) -> Dict:
        """Get comprehensive rate limit information"""
        
        info = {
            "user_id": user_id,
            "ip": self._get_client_ip(request),
            "user_tier": self.get_user_tier(user_id) if user_id else "anonymous",
            "limits": {}
        }
        
        applicable_rules = self._get_applicable_rules(
            user_id=user_id,
            endpoint=None,  # Get all rules
            ip=info["ip"]
        )
        
        for rule_id, rule in applicable_rules:
            key = self._generate_key(rule, user_id, info["ip"])
            status = await self._check_rule(rule, key)
            
            info["limits"][rule_id] = {
                "max_requests": rule.max_requests,
                "window_seconds": rule.window_seconds,
                "requests_made": status.requests_made,
                "requests_remaining": status.requests_remaining,
                "reset_time": status.reset_time.isoformat(),
                "is_limited": status.is_limited
            }
        
        return info


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic rate limiting
    """
    
    def __init__(self, app, rate_limiter: AdvancedRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Extract user ID from JWT token or session
        user_id = await self._extract_user_id(request)
        endpoint = request.url.path
        
        # Check rate limits
        try:
            status = await self.rate_limiter.check_rate_limit(
                request=request,
                user_id=user_id,
                endpoint=endpoint
            )
            
            # Handle rate limit exceeded
            if status.is_limited:
                if status.action == RateLimitAction.BLOCK:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "Rate limit exceeded",
                            "retry_after": status.retry_after,
                            "requests_remaining": status.requests_remaining,
                            "reset_time": status.reset_time.isoformat()
                        },
                        headers={"Retry-After": str(status.retry_after)}
                    )
                elif status.action == RateLimitAction.THROTTLE:
                    # Add artificial delay
                    rule = next((r for r in self.rate_limiter.rules.values() 
                               if r.action == RateLimitAction.THROTTLE), None)
                    if rule:
                        await asyncio.sleep(rule.throttle_delay)
            
            # Process request
            response = await call_next(request)
            
            # Record successful request
            await self.rate_limiter.record_request(
                request=request,
                user_id=user_id,
                endpoint=endpoint
            )
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Remaining"] = str(status.requests_remaining)
            response.headers["X-RateLimit-Reset"] = str(int(status.reset_time.timestamp()))
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue processing on rate limiter errors
            return await call_next(request)
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (implement based on your auth system)"""
        
        # Check for JWT token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # Decode JWT token to get user ID
            # This is a simplified example - implement proper JWT validation
            try:
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("user_id")
            except:
                pass
        
        # Check for session cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            # Look up user ID from session store
            # Implement based on your session management
            pass
        
        return None


# Usage example and configuration
def create_rate_limiter(redis_url: Optional[str] = None) -> AdvancedRateLimiter:
    """Create and configure a rate limiter instance"""
    
    redis_client = None
    if redis_url:
        redis_client = redis.from_url(redis_url)
    
    limiter = AdvancedRateLimiter(redis_client)
    
    # Add custom rules for specific use cases
    limiter.add_rule("habit_completion", RateLimitRule(
        max_requests=50,  # Max 50 habit completions per hour
        window_seconds=3600,
        limit_type=RateLimitType.USER_BASED,
        endpoints=["/habits/*/complete"],
        action=RateLimitAction.THROTTLE,
        throttle_delay=1.0
    ))
    
    limiter.add_rule("analytics_queries", RateLimitRule(
        max_requests=200,  # Max 200 analytics queries per hour
        window_seconds=3600,
        limit_type=RateLimitType.USER_BASED,
        endpoints=["/analytics/*"],
        burst_allowance=20
    ))
    
    return limiter


# FastAPI dependency for rate limiting
async def get_rate_limit_info(request: Request, 
                             rate_limiter: AdvancedRateLimiter) -> Dict:
    """FastAPI dependency to get rate limit information"""
    
    user_id = await RateLimitMiddleware(None, rate_limiter)._extract_user_id(request)
    return await rate_limiter.get_rate_limit_info(request, user_id)