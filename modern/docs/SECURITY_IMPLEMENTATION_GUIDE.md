# Security Implementation Guide

## Overview

This comprehensive guide documents the security implementation for The Wizard's Grimoire application, providing detailed instructions for developers, system administrators, and security teams.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [Input Validation](#input-validation)
5. [Rate Limiting](#rate-limiting)
6. [Security Headers](#security-headers)
7. [GDPR Compliance](#gdpr-compliance)
8. [Monitoring & Logging](#monitoring--logging)
9. [Development Guidelines](#development-guidelines)
10. [Deployment Security](#deployment-security)

## Security Architecture

### Multi-Layer Defense Strategy

The application implements defense in depth with multiple security layers:

```
User -> WAF -> Load Balancer -> API Gateway -> Application -> Database
  |      |          |              |              |            |
  |      |          |              |              |            |
  v      v          v              v              v            v
Auth   DDoS      TLS/mTLS      Rate Limiting   Input Val    Encryption
      Protection            & API Security   & Sanitization  at Rest
```

### Core Security Components

#### 1. Authentication System (`modern/backend/auth.py`)

**Implementation**: JWT-based authentication with 2FA support

```python
# Key Features:
- JWT token generation and validation
- TOTP-based 2FA implementation
- Secure password hashing with bcrypt
- Token refresh mechanism
- Account lockout protection
```

**Configuration**:

```python
# Environment Variables
JWT_SECRET_KEY=<secure-random-key>
JWT_EXPIRY_HOURS=8
TOTP_ISSUER=WizardsGrimoire
ENABLE_2FA=true
```

#### 2. Authorization Middleware (`modern/backend/rbac.py`)

**Implementation**: Role-Based Access Control (RBAC)

```python
# Role Hierarchy:
USER < MODERATOR < ADMIN < SUPER_ADMIN

# Permission System:
- Resource-based permissions
- Action-based controls (read, write, delete)
- Hierarchical role inheritance
- Dynamic permission checking
```

#### 3. Input Validation (`modern/backend/schemas.py`)

**Implementation**: Pydantic-based validation with custom validators

```python
# Validation Rules:
- Email format validation
- Password complexity requirements
- SQL injection prevention
- XSS protection through sanitization
- File upload validation
```

## Authentication & Authorization

### JWT Implementation

#### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "uuid",
    "email": "user@example.com",
    "roles": ["user"],
    "exp": 1693440000,
    "iat": 1693440000,
    "jti": "token-id"
  }
}
```

#### Security Features

- **Secure Storage**: HTTPOnly cookies with secure flag
- **Token Rotation**: Automatic refresh on activity
- **Revocation**: Centralized token blacklist
- **Expiration**: Configurable token lifetimes

### Two-Factor Authentication (2FA)

#### Setup Process

1. User enables 2FA in account settings
2. Server generates TOTP secret
3. QR code displayed for authenticator app
4. User verifies with backup codes
5. 2FA enforced on subsequent logins

#### Implementation Details

```python
# TOTP Configuration
SECRET_LENGTH = 32
TOTP_WINDOW = 1  # ±30 seconds
BACKUP_CODES = 8  # Generated per user
```

### Role-Based Access Control

#### Role Definitions

```python
ROLES = {
    "user": {
        "permissions": ["read_own_data", "write_own_data"],
        "level": 1
    },
    "moderator": {
        "permissions": ["read_user_data", "moderate_content"],
        "level": 2,
        "inherits": ["user"]
    },
    "admin": {
        "permissions": ["manage_users", "system_config"],
        "level": 3,
        "inherits": ["moderator"]
    }
}
```

#### Permission Checking

```python
@require_permission("manage_users")
async def admin_endpoint(request: Request):
    # Only accessible to users with manage_users permission
    pass
```

## Data Protection

### Encryption at Rest

#### Database Encryption

- **Algorithm**: AES-256-GCM
- **Key Management**: Environment variables with rotation
- **Scope**: PII, passwords, sensitive user data

#### Implementation

```python
# Encrypted field example
class User(Base):
    id = Column(UUID, primary_key=True)
    email = Column(String)  # Not encrypted (indexable)
    phone = Column(EncryptedType(String))  # Encrypted
    password_hash = Column(String)  # Hashed, not encrypted
```

### Encryption in Transit

#### TLS Configuration

- **Version**: TLS 1.3 minimum
- **Cipher Suites**: AEAD ciphers only
- **Certificate**: Let's Encrypt with auto-renewal

#### API Security

```python
# All API endpoints require HTTPS
FORCE_HTTPS = True
HSTS_ENABLE = True
HSTS_MAX_AGE = 31536000  # 1 year
```

### Data Classification

#### Classification Levels

1. **Public**: Can be freely shared
2. **Internal**: Company internal use
3. **Confidential**: Access on need-to-know basis
4. **Restricted**: Highest protection level

#### Handling Guidelines

```python
# Data classification in code
@classify_data("confidential")
class UserProfile:
    # Automatically applies appropriate protection
    pass
```

## Input Validation

### Validation Framework

#### Pydantic Schemas

```python
class UserCreateSchema(BaseModel):
    email: EmailStr
    password: SecurePassword
    name: str = Field(..., min_length=1, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        return validate_password_strength(v)
```

#### Custom Validators

```python
def validate_password_strength(password: str) -> str:
    """
    Password Requirements:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    - No common passwords
    """
    # Implementation details...
```

### SQL Injection Prevention

#### Parameterized Queries

```python
# Safe - parameterized query
query = "SELECT * FROM users WHERE email = %s"
result = cursor.execute(query, (user_email,))

# Unsafe - string concatenation (never do this)
query = f"SELECT * FROM users WHERE email = '{user_email}'"
```

#### ORM Usage

```python
# SQLAlchemy automatically prevents SQL injection
user = session.query(User).filter(User.email == email).first()
```

### XSS Prevention

#### Content Security Policy

```http
Content-Security-Policy: default-src 'self';
                        script-src 'self' 'unsafe-inline';
                        style-src 'self' 'unsafe-inline';
                        img-src 'self' data: https:;
```

#### Output Encoding

```python
from html import escape

def sanitize_output(content: str) -> str:
    """Escape HTML entities to prevent XSS"""
    return escape(content)
```

## Rate Limiting

### Implementation Strategy

#### Sliding Window Algorithm

```python
# Rate limit configuration
RATE_LIMITS = {
    "auth": "5/minute",      # Authentication endpoints
    "api": "100/minute",     # General API endpoints
    "upload": "10/hour",     # File upload endpoints
    "export": "3/hour"       # Data export endpoints
}
```

#### Redis-Based Tracking

```python
class RateLimitMiddleware:
    def __init__(self):
        self.redis = Redis.from_url(os.getenv('REDIS_URL'))

    async def check_rate_limit(self, key: str, limit: int, window: int):
        # Sliding window implementation
        pass
```

### Advanced Features

#### IP-Based Blocking

```python
# Automatic IP blocking after excessive violations
BLOCK_THRESHOLDS = {
    "failed_auth": 10,       # Block after 10 failed auth attempts
    "rate_limit": 5,         # Block after 5 rate limit violations
    "suspicious": 3          # Block after 3 suspicious activities
}
```

#### Whitelist Management

```python
# Whitelist trusted IPs (admin access, monitoring)
RATE_LIMIT_WHITELIST = [
    "192.168.1.0/24",       # Internal network
    "10.0.0.0/8",           # Corporate VPN
]
```

## Security Headers

### Comprehensive Header Implementation

#### Security Headers Middleware

```python
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

#### Content Security Policy (CSP)

```python
def build_csp_header():
    """Build CSP header based on environment"""
    if is_development():
        # More permissive for development
        return "default-src 'self' 'unsafe-inline' 'unsafe-eval'"
    else:
        # Strict for production
        return "default-src 'self'; script-src 'self'"
```

## GDPR Compliance

### Data Subject Rights Implementation

#### Right of Access

```python
@app.post("/api/gdpr/export")
async def export_user_data(user_id: str):
    """Export all user data in portable format"""
    data = await gdpr_service.export_user_data(user_id)
    return {"data": data, "format": "json"}
```

#### Right to Be Forgotten

```python
@app.delete("/api/gdpr/delete")
async def delete_user_account(user_id: str, verification_code: str):
    """Permanently delete user account and data"""
    if await verify_deletion_code(user_id, verification_code):
        await gdpr_service.delete_user_data(user_id)
        return {"status": "deleted"}
```

#### Data Retention Policies

```python
RETENTION_POLICIES = {
    "user_accounts": timedelta(days=7*365),      # 7 years
    "user_habits": timedelta(days=3*365),        # 3 years
    "analytics_data": timedelta(days=2*365),     # 2 years
    "security_logs": timedelta(days=1*365),      # 1 year
    "audit_logs": timedelta(days=7*365)          # 7 years
}
```

### Privacy by Design

#### Data Minimization

```python
class UserRegistration:
    # Only collect necessary data
    email: str          # Required for authentication
    password: str       # Required for security
    name: str          # Required for personalization
    # phone: Optional   # Only collect if needed
```

#### Purpose Limitation

```python
@track_data_usage("analytics")
def collect_usage_metrics(user_id: str, action: str):
    """Track usage only for specified analytics purpose"""
    pass
```

## Monitoring & Logging

### Security Event Logging

#### Structured Logging

```python
import structlog

security_logger = structlog.get_logger("security")

def log_auth_attempt(user_id: str, success: bool, ip: str):
    security_logger.info(
        "authentication_attempt",
        user_id=user_id,
        success=success,
        source_ip=ip,
        timestamp=datetime.utcnow().isoformat()
    )
```

#### Log Categories

```python
LOG_CATEGORIES = {
    "authentication": ["login", "logout", "2fa", "password_reset"],
    "authorization": ["permission_denied", "role_change"],
    "data_access": ["read", "write", "delete", "export"],
    "security_events": ["suspicious_activity", "rate_limit", "blocked_ip"]
}
```

### Real-Time Monitoring

#### Security Metrics

```python
MONITORED_METRICS = {
    "failed_auth_rate": "Failed authentication attempts per minute",
    "suspicious_ip_count": "Number of IPs with suspicious activity",
    "rate_limit_violations": "Rate limit violations per hour",
    "data_export_requests": "GDPR data export requests per day"
}
```

#### Alert Thresholds

```python
ALERT_THRESHOLDS = {
    "failed_auth_rate": 10,      # Alert if >10 failures/minute
    "suspicious_activity": 5,     # Alert if >5 suspicious events
    "data_breach_indicators": 1   # Alert immediately
}
```

## Development Guidelines

### Secure Coding Practices

#### Code Review Checklist

- [ ] Input validation on all user inputs
- [ ] Parameterized queries for database access
- [ ] Proper error handling without information disclosure
- [ ] Authentication and authorization checks
- [ ] Secure data storage (encryption for sensitive data)
- [ ] Security headers implementation
- [ ] GDPR compliance for data processing

#### Testing Requirements

```python
# Security test example
def test_sql_injection_protection():
    malicious_input = "'; DROP TABLE users; --"
    response = client.post("/api/search", json={"query": malicious_input})
    assert response.status_code == 400  # Should be rejected
```

### Environment Management

#### Development vs Production

```python
# Development settings
if ENVIRONMENT == "development":
    DEBUG = True
    CORS_ALLOW_ALL = True
    RATE_LIMIT_DISABLED = True

# Production settings
elif ENVIRONMENT == "production":
    DEBUG = False
    CORS_ALLOW_ALL = False
    FORCE_HTTPS = True
    HSTS_ENABLE = True
```

#### Secret Management

```bash
# Use environment variables for secrets
export JWT_SECRET_KEY=$(openssl rand -base64 32)
export DATABASE_PASSWORD=$(vault kv get -field=password secret/db)
export ENCRYPTION_KEY=$(vault kv get -field=key secret/encryption)
```

## Deployment Security

### Container Security

#### Dockerfile Best Practices

```dockerfile
# Use specific version tags
FROM python:3.11-slim

# Create non-root user
RUN adduser --system --group appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y

# Set secure permissions
COPY --chown=appuser:appuser . /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD curl -f http://localhost:8000/health || exit 1
```

#### Docker Compose Security

```yaml
version: "3.8"
services:
  app:
    build: .
    user: "1000:1000"
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
    internal: true
```

### Infrastructure Security

#### Network Segmentation

```yaml
# docker-compose.yml network configuration
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true # No external access
  database:
    driver: bridge
    internal: true # Database isolated
```

#### TLS Configuration

```nginx
# Nginx TLS configuration
ssl_protocols TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_stapling on;
ssl_stapling_verify on;
```

## Security Maintenance

### Regular Security Tasks

#### Weekly Tasks

- [ ] Review security logs for anomalies
- [ ] Check for new security advisories
- [ ] Validate backup integrity
- [ ] Update threat intelligence feeds

#### Monthly Tasks

- [ ] Security dependency updates
- [ ] Access review and cleanup
- [ ] Vulnerability scanning
- [ ] Incident response plan review

#### Quarterly Tasks

- [ ] Penetration testing
- [ ] Security awareness training
- [ ] Compliance audit
- [ ] Disaster recovery testing

### Incident Response

#### Immediate Response (0-15 minutes)

1. Identify and classify the incident
2. Activate incident response team
3. Contain the threat
4. Preserve evidence

#### Short-term Response (15 minutes - 2 hours)

1. Investigate root cause
2. Eradicate the threat
3. Begin recovery procedures
4. Notify stakeholders

#### Long-term Response (2+ hours)

1. Complete system recovery
2. Conduct post-incident review
3. Update security measures
4. Document lessons learned

## Compliance Frameworks

### GDPR Compliance Checklist

- [ ] Privacy policy published and accessible
- [ ] Consent mechanisms implemented
- [ ] Data subject rights functionality
- [ ] Data protection impact assessments
- [ ] Data breach notification procedures
- [ ] Privacy by design principles

### Security Standards Alignment

- [ ] OWASP Top 10 protection
- [ ] NIST Cybersecurity Framework
- [ ] ISO 27001 controls implementation
- [ ] SOC 2 Type II readiness

## Troubleshooting

### Common Security Issues

#### Authentication Problems

```python
# Debug authentication issues
def debug_auth_failure(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"status": "valid", "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"status": "expired"}
    except jwt.InvalidTokenError:
        return {"status": "invalid"}
```

#### Rate Limiting Issues

```python
# Check rate limit status
def check_rate_limit_status(ip: str):
    key = f"rate_limit:{ip}"
    current = redis.get(key)
    ttl = redis.ttl(key)
    return {"current": current, "ttl": ttl}
```

#### GDPR Compliance Issues

```python
# Verify GDPR compliance status
def check_gdpr_compliance(user_id: str):
    user = get_user(user_id)
    return {
        "data_retention_compliant": check_retention_policy(user),
        "consent_status": check_consent_status(user),
        "data_processing_legal": check_legal_basis(user)
    }
```

---

**Document Version**: 1.0  
**Last Updated**: August 30, 2025  
**Next Review**: November 30, 2025  
**Maintained By**: Security Team
