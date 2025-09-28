import time
import os
from typing import Dict, Tuple, Optional, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from config import settings
from security_monitor import security_monitor, log_rate_limit_exceeded, check_ip_blocked


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = self._get_security_headers()
    
    def _get_security_headers(self):
        """Get comprehensive security headers configuration"""
        return {
            # Content Security Policy
            "Content-Security-Policy": settings.csp_header(),
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # XSS Protection (legacy but still useful)
            "X-XSS-Protection": "1; mode=block",
            
            # Prevent framing
            "X-Frame-Options": "DENY",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy (Feature Policy successor)
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), "
                "accelerometer=(), ambient-light-sensor=(), "
                "autoplay=(), encrypted-media=(), fullscreen=(), "
                "picture-in-picture=()"
            ),
            
            # Cross-Origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            
            # Additional security headers
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-DNS-Prefetch-Control": "off",
            "Expect-CT": "max-age=86400, enforce",
            
            # Cache control for sensitive pages
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Server information hiding
            "Server": "WizardsGrimoire/1.0",
            "X-Powered-By": "Magic",
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Apply security headers
        for header_name, header_value in self.security_headers.items():
            # Skip cache headers for static resources
            if (header_name in ["Cache-Control", "Pragma", "Expires"] and
                    self._is_static_resource(request.url.path)):
                continue
                
            response.headers[header_name] = header_value
        
        # HSTS (only for HTTPS)
        if settings.HSTS_ENABLE and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Remove potentially revealing headers
        headers_to_remove = ["server", "x-powered-by", "x-aspnet-version"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]
        
        # Add API version and security level info
        if request.url.path.startswith("/api/"):
            response.headers["X-API-Version"] = "v1"
            response.headers["X-Security-Level"] = "enhanced"
            response.headers["X-Content-Security"] = "validated"
        
        return response
    
    def _is_static_resource(self, path: str) -> bool:
        """Check if the path is for a static resource"""
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', 
                           '.svg', '.ico', '.woff', '.woff2', '.ttf']
        return any(path.endswith(ext) for ext in static_extensions)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_bytes: int):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes
        
        # Per-endpoint size limits
        self.endpoint_limits = {
            # File upload endpoints
            "/api/files/upload": 50 * 1024 * 1024,  # 50MB for file uploads
            "/api/profile/avatar": 5 * 1024 * 1024,   # 5MB for avatar uploads
            
            # Data export endpoints  
            "/api/gdpr/export-data": 100 * 1024 * 1024,  # 100MB for export
            
            # Authentication endpoints (strict limits)
            "/api/auth/login": 1024,  # 1KB for login
            "/api/auth/register": 2048,  # 2KB for registration
            "/api/auth/2fa": 1024,  # 1KB for 2FA
            
            # Application data endpoints
            "/api/habits": 10 * 1024,  # 10KB for habit operations
            "/api/projects": 50 * 1024,  # 50KB for project operations
            
            # Admin endpoints
            "/api/admin/": 1024 * 1024,  # 1MB for admin operations
        }

    def _get_size_limit_for_path(self, path: str) -> int:
        """Get appropriate size limit for the given path"""
        # Check exact matches first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check prefix matches for admin endpoints
        for endpoint_path, limit in self.endpoint_limits.items():
            if endpoint_path.endswith("/") and path.startswith(endpoint_path):
                return limit
        
        # Return default limit
        return self.max_body_bytes

    async def dispatch(self, request: Request, call_next):
        # Skip when no body (GET/DELETE/etc.)
        if request.method in {"GET", "DELETE", "OPTIONS", "HEAD"}:
            return await call_next(request)

        # Get appropriate size limit for this endpoint
        size_limit = self._get_size_limit_for_path(request.url.path)
        
        cl = request.headers.get("content-length")
        try:
            if cl and int(cl) > size_limit:
                return JSONResponse(
                    {
                        "detail": "request entity too large",
                        "max_size": size_limit,
                        "received_size": int(cl)
                    }, 
                    status_code=413
                )
        except Exception:
            pass

        # Read body once and reuse cached body downstream
        body = await request.body()
        if len(body) > size_limit:
            return JSONResponse(
                {
                    "detail": "request entity too large",
                    "max_size": size_limit,
                    "received_size": len(body)
                }, 
                status_code=413
            )
        # Starlette caches body in request, so downstream can still call .json()/.form()
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiter (windowed per minute).

    Uses Redis when REDIS_URL is configured; falls back to in-memory otherwise.
    """

    def __init__(self, app, requests_per_minute: int):
        super().__init__(app)
        self.rpm = max(1, int(requests_per_minute))
        self._counts: Dict[Tuple[str, int], int] = {}
        self._redis = self._init_redis()
        # Special rate limits for authentication endpoints
        self.auth_rpm = max(1, int(requests_per_minute // 4))  # More restrictive for auth

    def _init_redis(self):
        import os
        url = os.getenv('REDIS_URL')
        if not url:
            return None
        try:
            from redis import Redis
            return Redis.from_url(url)
        except Exception:
            return None

    def _client_ip(self, request: Request) -> str:
        # Prefer X-Forwarded-For first value if provided by a trusted proxy
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Don't limit CORS preflights
        if request.method == "OPTIONS":
            return await call_next(request)

        # Use stricter limits for authentication endpoints
        current_rpm = self.rpm
        path = request.url.path
        if any(auth_path in path for auth_path in ['/auth/login', '/auth/signup', '/2fa/']):
            current_rpm = self.auth_rpm

        now = int(time.time())
        window = now // 60
        ip = self._client_ip(request)
        if self._redis is not None:
            # Use a single Redis counter per ip+window
            rkey = f"rl:{ip}:{window}"
            try:
                # Redis incr returns an integer
                redis_result = self._redis.incr(rkey)
                # Type safety: ensure we have an integer
                current = redis_result if isinstance(redis_result, int) else 1
                
                if current == 1:
                    # Set TTL to end of current minute
                    self._redis.expire(rkey, 60 - (now % 60))
                    
                if current > current_rpm:
                    retry_after = 60 - (now % 60)
                    return JSONResponse(
                        {"detail": "rate limit exceeded"},
                        status_code=429,
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(current_rpm),
                            "X-RateLimit-Remaining": "0",
                        },
                    )
                resp: Response = await call_next(request)
                remaining = max(0, current_rpm - current)
                resp.headers.setdefault("X-RateLimit-Limit", str(current_rpm))
                resp.headers.setdefault(
                    "X-RateLimit-Remaining", str(remaining)
                )
                return resp
            except Exception:
                # If Redis fails, fall back to memory
                pass

        # In-memory windowing fallback
        key = (ip, window)
        count = self._counts.get(key, 0)
        if count >= current_rpm:
            retry_after = 60 - (now % 60)
            return JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(current_rpm),
                    "X-RateLimit-Remaining": "0",
                },
            )
        self._counts[key] = count + 1
        resp: Response = await call_next(request)
        remaining = max(0, current_rpm - self._counts.get(key, 0))
        resp.headers.setdefault("X-RateLimit-Limit", str(current_rpm))
        resp.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        return resp


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection for
    cookie-authenticated, state-changing requests.

    Enforced when settings.CSRF_ENABLE is true and request has a
    session cookie and no Bearer token.
    Excludes safe methods and OPTIONS.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if not settings.CSRF_ENABLE:
            return await call_next(request)

        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # If using Bearer token, skip CSRF (not cookie-based auth)
        auth_header = (request.headers.get('authorization') or
                       request.headers.get('Authorization'))
        if auth_header and auth_header.lower().startswith('bearer '):
            return await call_next(request)

        # Only enforce if session cookie present
        if request.cookies.get('session'):
            csrf_header = (request.headers.get(settings.CSRF_HEADER_NAME) or
                           request.headers.get(
                               settings.CSRF_HEADER_NAME.upper()))
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            if (not csrf_header or not csrf_cookie or
                    csrf_header != csrf_cookie):
                return JSONResponse(
                    {"detail": "CSRF token missing or invalid"},
                    status_code=403
                )
        return await call_next(request)
