"""
API versioning and security middleware
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Set
import re

from secure_logging import security_logger


class APIVersioningSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API versioning and security policies"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Current supported API versions
        self.supported_versions = {"v1", "v2"}
        self.default_version = "v1"
        self.deprecated_versions = {"v1"}  # v1 is deprecated but still supported
        
        # Version-specific security policies
        self.version_policies = {
            "v1": {
                "rate_limit_multiplier": 0.5,  # 50% of normal rate limit
                "require_2fa": False,
                "max_request_size": 1024 * 1024,  # 1MB
                "allowed_endpoints": {
                    "/api/v1/auth/*",
                    "/api/v1/habits/*", 
                    "/api/v1/projects/*",
                    "/api/v1/user/*"
                }
            },
            "v2": {
                "rate_limit_multiplier": 1.0,  # Full rate limit
                "require_2fa": True,
                "max_request_size": 10 * 1024 * 1024,  # 10MB
                "allowed_endpoints": {
                    "/api/v2/auth/*",
                    "/api/v2/habits/*",
                    "/api/v2/projects/*", 
                    "/api/v2/user/*",
                    "/api/v2/admin/*",
                    "/api/v2/gdpr/*"
                }
            }
        }
    
    def _extract_version_from_path(self, path: str) -> str:
        """Extract API version from request path"""
        # Match patterns like /api/v1/... or /api/v2/...
        version_match = re.match(r'^/api/(v\d+)/', path)
        if version_match:
            return version_match.group(1)
        
        # If no version in path, return default
        return self.default_version
    
    def _extract_version_from_header(self, request: Request) -> str:
        """Extract API version from Accept header"""
        accept_header = request.headers.get("accept", "")
        
        # Match patterns like application/vnd.wizardsgrimoire.v2+json
        version_match = re.search(r'application/vnd\.wizardsgrimoire\.(v\d+)', accept_header)
        if version_match:
            return version_match.group(1)
        
        # Check custom API-Version header
        api_version = request.headers.get("api-version")
        if api_version and api_version in self.supported_versions:
            return api_version
        
        return None
    
    def _is_endpoint_allowed(self, path: str, version: str) -> bool:
        """Check if endpoint is allowed for the given API version"""
        allowed_endpoints = self.version_policies.get(version, {}).get("allowed_endpoints", set())
        
        for allowed_pattern in allowed_endpoints:
            if allowed_pattern.endswith("*"):
                # Wildcard match
                prefix = allowed_pattern[:-1]
                if path.startswith(prefix):
                    return True
            elif path == allowed_pattern:
                # Exact match
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with API versioning security"""
        try:
            # Extract API version from path or headers
            path_version = self._extract_version_from_path(request.url.path)
            header_version = self._extract_version_from_header(request)
            
            # Determine final version (header takes precedence)
            api_version = header_version if header_version else path_version
            
            # Validate API version
            if api_version not in self.supported_versions:
                security_logger.warning(
                    f"Unsupported API version requested: {api_version}",
                    extra={
                        "client_ip": self._get_client_ip(request),
                        "path": request.url.path,
                        "requested_version": api_version,
                        "user_agent": request.headers.get("user-agent", "unknown")
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Unsupported API version",
                        "requested_version": api_version,
                        "supported_versions": list(self.supported_versions),
                        "message": f"Please use API version {self.default_version} or {max(self.supported_versions)}"
                    }
                )
            
            # Check if endpoint is allowed for this version
            if not self._is_endpoint_allowed(request.url.path, api_version):
                security_logger.warning(
                    f"Endpoint not available in API version {api_version}: {request.url.path}",
                    extra={
                        "client_ip": self._get_client_ip(request),
                        "path": request.url.path,
                        "api_version": api_version
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "error": "Endpoint not available in this API version",
                        "api_version": api_version,
                        "path": request.url.path
                    }
                )
            
            # Add deprecation warning for deprecated versions
            response = await call_next(request)
            
            if api_version in self.deprecated_versions:
                response.headers["Warning"] = f"299 - \"API version {api_version} is deprecated. Please upgrade to version {max(self.supported_versions)}.\""
                response.headers["Sunset"] = "Sat, 31 Dec 2024 23:59:59 GMT"  # Deprecation date
            
            # Add API version to response headers
            response.headers["API-Version"] = api_version
            response.headers["API-Supported-Versions"] = ",".join(sorted(self.supported_versions))
            
            # Store version info in request state for other middleware
            request.state.api_version = api_version
            request.state.version_policies = self.version_policies.get(api_version, {})
            
            return response
            
        except Exception as e:
            security_logger.error(
                f"API versioning middleware error: {str(e)}",
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
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class APISecurityEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforce version-specific security policies"""
    
    async def dispatch(self, request: Request, call_next):
        """Enforce security policies based on API version"""
        # Skip if no version info (set by APIVersioningSecurityMiddleware)
        if not hasattr(request.state, 'api_version'):
            return await call_next(request)
        
        version_policies = getattr(request.state, 'version_policies', {})
        
        # Enforce 2FA requirement for certain versions
        if version_policies.get('require_2fa', False):
            # Check if user has 2FA enabled (this would integrate with auth system)
            auth_header = request.headers.get("authorization", "")
            if auth_header and "Bearer" in auth_header:
                # In real implementation, decode JWT and check 2FA status
                # For now, just log the requirement
                security_logger.info(
                    f"2FA required for API version {request.state.api_version}",
                    extra={
                        "path": request.url.path,
                        "api_version": request.state.api_version
                    }
                )
        
        response = await call_next(request)
        
        # Add security headers based on version
        if hasattr(request.state, 'api_version'):
            if request.state.api_version in ["v2"]:
                # Enhanced security for newer API versions
                response.headers["X-API-Security-Level"] = "enhanced"
                response.headers["X-Content-Type-Options"] = "nosniff"
            else:
                response.headers["X-API-Security-Level"] = "standard"
        
        return response