"""
Request size limiting middleware for API security
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from secure_logging import security_logger


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request size limits"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
        self.endpoint_limits = {
            # File upload endpoints
            "/api/files/upload": 50 * 1024 * 1024,  # 50MB for file uploads
            "/api/profile/avatar": 5 * 1024 * 1024,   # 5MB for avatar uploads
            
            # Data export endpoints
            "/api/gdpr/export-data": 100 * 1024 * 1024,  # 100MB for data export
            
            # API endpoints with stricter limits
            "/api/auth/login": 1024,  # 1KB for login
            "/api/auth/register": 2048,  # 2KB for registration
            "/api/habits": 10 * 1024,  # 10KB for habit operations
            "/api/projects": 50 * 1024,  # 50KB for project operations
            
            # Admin endpoints
            "/api/admin/*": 1024 * 1024,  # 1MB for admin operations
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with size validation"""
        try:
            # Get content length from headers
            content_length = request.headers.get("content-length")
            
            if content_length:
                content_length = int(content_length)
                max_allowed = self._get_size_limit_for_endpoint(request.url.path)
                
                if content_length > max_allowed:
                    security_logger.warning(
                        f"Request size limit exceeded: {content_length} bytes "
                        f"(max: {max_allowed}) for {request.url.path}",
                        extra={
                            "client_ip": self._get_client_ip(request),
                            "path": request.url.path,
                            "size": content_length,
                            "limit": max_allowed,
                            "user_agent": request.headers.get("user-agent", "unknown")
                        }
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request too large",
                            "max_size": max_allowed,
                            "received_size": content_length
                        }
                    )
            
            # Process request
            response = await call_next(request)
            return response
            
        except ValueError:
            # Invalid content-length header
            security_logger.warning(
                f"Invalid content-length header for {request.url.path}",
                extra={
                    "client_ip": self._get_client_ip(request),
                    "path": request.url.path,
                    "content_length_header": request.headers.get("content-length")
                }
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid content-length header"}
            )
        except Exception as e:
            security_logger.error(
                f"Request size middleware error: {str(e)}",
                extra={
                    "client_ip": self._get_client_ip(request),
                    "path": request.url.path,
                    "error": str(e)
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    def _get_size_limit_for_endpoint(self, path: str) -> int:
        """Get size limit for specific endpoint"""
        # Check exact matches first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check wildcard matches
        for pattern, limit in self.endpoint_limits.items():
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if path.startswith(prefix):
                    return limit
        
        # Return default limit
        return self.max_size
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"


class StreamingRequestSizeValidator:
    """Validator for streaming request body size"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.current_size = 0
    
    async def validate_chunk(self, chunk: bytes) -> bool:
        """Validate individual chunk and update size counter"""
        self.current_size += len(chunk)
        
        if self.current_size > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large. Max size: {self.max_size} bytes"
            )
        
        return True


async def validate_request_size(
    request: Request, max_size: Optional[int] = None
):
    """Helper function to validate request size in route handlers"""
    if max_size is None:
        max_size = 10 * 1024 * 1024  # 10MB default
    
    content_length = request.headers.get("content-length")
    
    if content_length:
        try:
            content_length = int(content_length)
            if content_length > max_size:
                security_logger.warning(
                    f"Request size validation failed: {content_length} > {max_size}",
                    extra={
                        "path": request.url.path,
                        "size": content_length,
                        "limit": max_size
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request too large. Max size: {max_size} bytes"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content-length header"
            )
