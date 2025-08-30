import time
from typing import Dict, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from config import settings


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_bytes: int):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next):
        # Skip when no body (GET/DELETE/etc.)
        if request.method in {"GET", "DELETE", "OPTIONS", "HEAD"}:
            return await call_next(request)

        cl = request.headers.get("content-length")
        try:
            if cl and int(cl) > self.max_body_bytes:
                return JSONResponse({"detail": "request entity too large"}, status_code=413)
        except Exception:
            pass

        # Read body once and reuse cached body downstream
        body = await request.body()
        if len(body) > self.max_body_bytes:
            return JSONResponse({"detail": "request entity too large"}, status_code=413)
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

        now = int(time.time())
        window = now // 60
        ip = self._client_ip(request)
        if self._redis is not None:
            # Use a single Redis counter per ip+window
            rkey = f"rl:{ip}:{window}"
            try:
                current = self._redis.incr(rkey)
                if current == 1:
                    # Set TTL to end of current minute
                    self._redis.expire(rkey, 60 - (now % 60))
                if current > self.rpm:
                    retry_after = 60 - (now % 60)
                    return JSONResponse(
                        {"detail": "rate limit exceeded"},
                        status_code=429,
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(self.rpm),
                            "X-RateLimit-Remaining": "0",
                        },
                    )
                resp: Response = await call_next(request)
                remaining = max(0, self.rpm - int(current))
                resp.headers.setdefault("X-RateLimit-Limit", str(self.rpm))
                resp.headers.setdefault("X-RateLimit-Remaining", str(remaining))
                return resp
            except Exception:
                # If Redis fails, fall back to memory
                pass

        # In-memory windowing fallback
        key = (ip, window)
        count = self._counts.get(key, 0)
        if count >= self.rpm:
            retry_after = 60 - (now % 60)
            return JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rpm),
                    "X-RateLimit-Remaining": "0",
                },
            )
        self._counts[key] = count + 1
        resp: Response = await call_next(request)
        remaining = max(0, self.rpm - self._counts.get(key, 0))
        resp.headers.setdefault("X-RateLimit-Limit", str(self.rpm))
        resp.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        return resp


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection for cookie-authenticated, state-changing requests.

    Enforced when settings.CSRF_ENABLE is true and request has a session cookie and no Bearer token.
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
        auth = request.headers.get('authorization') or request.headers.get('Authorization')
        if auth and auth.lower().startswith('bearer '):
            return await call_next(request)

        # Only enforce if session cookie present
        if request.cookies.get('session'):
            header = request.headers.get(settings.CSRF_HEADER_NAME) or request.headers.get(settings.CSRF_HEADER_NAME.upper())
            cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            if not header or not cookie or header != cookie:
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)
        return await call_next(request)
