# LifeRPG Security Guide

This document outlines the security measures implemented in LifeRPG, vulnerability reporting procedures, and best practices for secure deployment.

## Table of Contents

1. [Security Model](#security-model)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [API Security](#api-security)
5. [Dependency Security](#dependency-security)
6. [Plugin Security](#plugin-security)
7. [Vulnerability Reporting](#vulnerability-reporting)
8. [Security Testing](#security-testing)
9. [Deployment Security](#deployment-security)
10. [Compliance & Privacy](#compliance--privacy)

## Security Model

LifeRPG implements a defense-in-depth security model with multiple layers of protection:

### Security Principles

- **Zero Trust**: All requests are authenticated and authorized regardless of source
- **Principle of Least Privilege**: Components only have access to what they need
- **Defense in Depth**: Multiple security controls at different layers
- **Secure by Default**: Security features enabled by default
- **Privacy by Design**: Data minimization and protection built-in

### Threat Model

Key threats addressed:

1. **Unauthorized Access**: Prevented through robust authentication and authorization
2. **Data Exposure**: Mitigated through encryption and access controls
3. **Injection Attacks**: Prevented through input validation and parameterized queries
4. **Cross-Site Scripting (XSS)**: Mitigated through content security policy and output encoding
5. **Cross-Site Request Forgery (CSRF)**: Prevented through anti-CSRF tokens
6. **Denial of Service**: Mitigated through rate limiting and resource controls
7. **Supply Chain Attacks**: Addressed through dependency scanning and SBOM
8. **Plugin Vulnerabilities**: Contained through sandboxing and permission controls

## Authentication & Authorization

### Authentication Methods

LifeRPG supports multiple secure authentication methods:

1. **OAuth2/OIDC**: Integration with identity providers using PKCE
   - Google, GitHub, Microsoft, etc.
   - Authorization code flow with PKCE for SPAs and mobile
   - Optional audience and issuer validation
   - RP-initiated logout support

2. **Two-Factor Authentication (2FA)**
   - TOTP (Time-based One-Time Password)
   - Recovery codes for backup access
   - Session management with primary/alt sessions

3. **API Tokens**
   - Fine-grained permissions
   - Expiring tokens with rotation
   - Token revocation support

### Token Security

- **JWT Security**: Short-lived tokens with proper signing
- **Secure Storage**: Tokens stored securely (HTTPOnly, Secure cookies)
- **Token Validation**: Thorough validation of token claims
- **Refresh Token Rotation**: One-time use refresh tokens

### Authorization

- **Role-Based Access Control (RBAC)**: User roles with specific permissions
- **Attribute-Based Access Control (ABAC)**: Fine-grained permissions based on attributes
- **Resource Ownership**: Users can only access their own data
- **Permission Checks**: Consistent permission validation throughout the application

Code example:
```python
# API endpoint with permission check
@router.get("/habits/{habit_id}", response_model=HabitRead)
async def get_habit(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    habit = await habit_service.get_habit(db, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Permission check
    if habit.user_id != current_user.id and not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return habit
```

## Data Protection

### Data at Rest

- **Database Encryption**: Sensitive fields encrypted in database
- **Secure Storage**: Secure storage options for sensitive user data
- **Encryption Keys**: Proper key management and rotation

### Data in Transit

- **TLS/HTTPS**: All communications encrypted with TLS 1.2+
- **HSTS**: HTTP Strict Transport Security enabled
- **Certificate Management**: Proper certificate validation and pinning

### Data Classification

Data is classified into sensitivity levels with appropriate controls:

1. **Public Data**: Non-sensitive, publicly accessible information
2. **User Data**: Personal data requiring authentication
3. **Sensitive Data**: Requiring additional protection (e.g., OAuth tokens)
4. **System Data**: Configuration and security settings

### Data Minimization

- **Purpose Limitation**: Data collected only for specific purposes
- **Storage Limitation**: Data retained only as long as necessary
- **Data Anonymization**: Personal data anonymized where possible

## API Security

### Input Validation

- **Schema Validation**: All inputs validated against Pydantic schemas
- **Type Checking**: Strong typing throughout the application
- **Sanitization**: Input sanitization for special contexts (e.g., HTML)

```python
# Input validation with Pydantic
class HabitCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    frequency: str = Field(..., pattern="^(daily|weekly|monthly|custom)$")
    xp_reward: int = Field(..., ge=1, le=100)
    
    @validator('title')
    def title_must_not_contain_html(cls, v):
        if re.search(r'<[^>]*>', v):
            raise ValueError('Title must not contain HTML tags')
        return v
```

### Request Limiting

- **Rate Limiting**: Per-user and per-IP rate limits
- **Concurrent Request Limiting**: Prevent resource exhaustion
- **Request Size Limiting**: Maximum body size enforced

```python
# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    rate=30,  # requests
    period=60,  # seconds
    storage=redis_storage,
    exclude_endpoints=["/health", "/metrics"],
)
```

### Security Headers

- **Content-Security-Policy (CSP)**: Restricts sources of executable scripts
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking
- **Referrer-Policy**: Controls referrer information
- **Permissions-Policy**: Restricts browser features

```python
# Security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    csp="default-src 'self'; script-src 'self'; connect-src 'self';",
    hsts=True,
    frame_options="DENY",
    content_type_options=True,
    referrer_policy="same-origin",
    permissions_policy="camera=(), microphone=(), geolocation=()",
)
```

### CSRF Protection

- **Double Submit Cookie**: CSRF token validation
- **Same-Site Cookies**: Cookies with SameSite=Lax/Strict
- **Origin Checking**: Validate Origin/Referer headers

## Dependency Security

### Software Bill of Materials (SBOM)

LifeRPG maintains a comprehensive SBOM that:

- Lists all direct and transitive dependencies
- Includes version information and licenses
- Is updated with each release
- Is available in both CycloneDX and SPDX formats

### Dependency Scanning

- **Automated Scanning**: Dependencies scanned for vulnerabilities
- **Regular Updates**: Dependencies kept up-to-date
- **Version Pinning**: Explicit version pinning for all dependencies
- **License Compliance**: Dependency licenses tracked and reviewed

Tools used:
- GitHub Dependabot
- OWASP Dependency Check
- Snyk

### Supply Chain Security

- **Verified Sources**: Dependencies from verified sources
- **Integrity Verification**: Package hashes verified
- **Reproducible Builds**: Deterministic build process
- **Secure CI/CD**: Pipeline security with proper secret management

## Plugin Security

### Sandbox Containment

Plugins run in a WebAssembly sandbox with:

- **Memory Isolation**: Protected memory space
- **CPU Limits**: Execution time and resource limits
- **I/O Restrictions**: Limited access to system resources
- **Network Controls**: Restricted network access

### Permission System

Plugins operate under a strict permission model:

- **Explicit Permissions**: Must request specific permissions
- **User Approval**: Permissions displayed and approved by users
- **Runtime Enforcement**: Permissions enforced during execution
- **Revocation**: Permissions can be revoked at any time

### Plugin Vetting

- **Automated Analysis**: Static and dynamic analysis of plugins
- **Code Review**: Optional review process for marketplace plugins
- **Reputation System**: User ratings and reviews
- **Revocation Mechanism**: Ability to disable malicious plugins

## Vulnerability Reporting

### Responsible Disclosure

We encourage responsible disclosure of security vulnerabilities:

1. **Reporting Channel**: Email security@liferpg.example.com or use our HackerOne page
2. **Encryption**: Use our PGP key for sensitive reports
3. **Response Timeline**: Initial response within 48 hours
4. **Disclosure Policy**: Coordinated disclosure after fixes
5. **Recognition**: Hall of Fame for security researchers

### Bug Bounty Program

LifeRPG offers a bug bounty program with:

- **Scope**: Defined in-scope and out-of-scope targets
- **Rewards**: Based on severity and impact
- **Rules of Engagement**: Clear testing guidelines
- **Safe Harbor**: Protection for good-faith security research

## Security Testing

### Automated Testing

- **SAST (Static Application Security Testing)**: Analyzes code for security issues
  - Tools: Bandit, ESLint security plugins, CodeQL
- **DAST (Dynamic Application Security Testing)**: Tests running application
  - Tools: OWASP ZAP, Burp Suite
- **Dependency Scanning**: Checks dependencies for vulnerabilities
  - Tools: Dependabot, Snyk, OWASP Dependency Check
- **Container Scanning**: Analyzes container images
  - Tools: Trivy, Clair

### Manual Testing

- **Penetration Testing**: Regular penetration tests
- **Code Reviews**: Security-focused code reviews
- **Threat Modeling**: Systematic analysis of threats
- **Red Team Exercises**: Simulated attacks to test defenses

### CI/CD Integration

Security testing is integrated into CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Security Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run SAST scan
        uses: github/codeql-action/analyze@v2
        
      - name: Run dependency scan
        uses: snyk/actions/python@master
        
      - name: Run container scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'liferpg/api:latest'
          
      - name: Run DAST scan
        uses: zaproxy/action-full-scan@v0.3.0
        with:
          target: 'http://localhost:8080'
```

## Deployment Security

### Secure Configuration

- **Environment Variables**: Sensitive configuration in environment variables
- **Secrets Management**: Secrets stored in vault systems
- **Configuration Validation**: Validation of security settings
- **Default Security**: Secure defaults with explicit opt-out

### Infrastructure Security

- **Container Security**: Minimal base images, non-root users
- **Network Security**: Network segmentation and firewalls
- **Cloud Security**: Follow cloud provider security best practices
- **Access Controls**: Least privilege for infrastructure access

### Monitoring & Logging

- **Security Monitoring**: Detection of unusual patterns
- **Centralized Logging**: Security-relevant events logged
- **Audit Trail**: Actions tracked for accountability
- **Alerting**: Automatic alerts for security events

### Incident Response

- **Response Plan**: Documented incident response procedure
- **Roles & Responsibilities**: Clear ownership during incidents
- **Communication Plan**: Internal and external communication
- **Post-Incident Analysis**: Learning from security incidents

## Compliance & Privacy

### Data Protection

- **GDPR Compliance**: European data protection regulations
- **CCPA Compliance**: California Consumer Privacy Act
- **Data Subject Rights**: Access, rectification, erasure
- **Data Processing Records**: Documentation of data processing

### Privacy Features

- **Privacy Policy**: Clear and comprehensive policy
- **Data Export**: User data export functionality
- **Data Deletion**: Complete account deletion option
- **Cookie Controls**: Minimal and controllable cookie usage

### Audit & Compliance

- **Security Audits**: Regular security assessments
- **Compliance Checks**: Verification of regulatory compliance
- **Documentation**: Comprehensive security documentation
- **Training**: Security awareness training for contributors

---

## Security Checklist

Use this checklist to verify LifeRPG's security implementation:

### Authentication & Authorization
- [ ] OAuth2/OIDC properly implemented with PKCE
- [ ] 2FA with TOTP available
- [ ] JWT tokens properly signed and validated
- [ ] Role-based access control implemented
- [ ] Resource ownership checks in place

### Data Protection
- [ ] Sensitive data encrypted in database
- [ ] TLS 1.2+ enforced for all connections
- [ ] HTTPS-only cookies
- [ ] Clear data retention policies

### API Security
- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] CSRF protection in place
- [ ] Request size limits enforced

### Dependency Security
- [ ] SBOM generated and maintained
- [ ] Dependency scanning in CI/CD
- [ ] Regular dependency updates
- [ ] License compliance verified

### Plugin Security
- [ ] WASM sandbox implemented
- [ ] Plugin permissions system working
- [ ] Resource limits enforced
- [ ] Plugin vetting process documented

### Deployment
- [ ] Secure configuration guide available
- [ ] Container security measures implemented
- [ ] Monitoring and logging in place
- [ ] Incident response plan documented

### Compliance
- [ ] Privacy policy up-to-date
- [ ] Data subject rights implemented
- [ ] Compliance documentation available
- [ ] Security training materials created
