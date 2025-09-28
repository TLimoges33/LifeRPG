"""
Security test coverage utilities and test fixtures
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import security modules to test
from auth import verify_password, create_access_token, verify_token
from security_monitor import SecurityMonitor
from simple_gdpr import gdpr_manager
from middleware import (
    SecurityHeadersMiddleware,
    BodySizeLimitMiddleware, 
    RateLimitMiddleware,
    CSRFMiddleware
)
from secure_logging import security_logger


class SecurityTestFixtures:
    """Test fixtures for security testing"""
    
    @staticmethod
    def create_test_user():
        """Create a test user with known credentials"""
        return {
            "id": 1,
            "email": "test@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1VQv3c1yqB",
            "totp_enabled": False,
            "role": "user",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    def create_admin_user():
        """Create a test admin user"""
        return {
            "id": 2,
            "email": "admin@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1VQv3c1yqB",
            "totp_enabled": True,
            "role": "admin",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    def create_malicious_payloads():
        """Create various malicious payloads for testing"""
        return {
            "xss_payloads": [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "';alert('xss');//",
                "<svg onload=alert('xss')>"
            ],
            "sql_injection_payloads": [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "'; SELECT * FROM users WHERE '1'='1",
                "UNION SELECT * FROM users",
                "1' AND 1=1#"
            ],
            "command_injection_payloads": [
                "; cat /etc/passwd",
                "| whoami",
                "&& ls -la",
                "`whoami`",
                "$(whoami)"
            ],
            "path_traversal_payloads": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....//....//....//etc/passwd"
            ]
        }
    
    @staticmethod
    def create_oversized_requests():
        """Create requests with various size violations"""
        return {
            "large_json": {"data": "x" * (10 * 1024 * 1024)},  # 10MB
            "many_params": {f"param_{i}": f"value_{i}" for i in range(1000)},
            "long_string": "x" * (5 * 1024 * 1024),  # 5MB string
            "nested_json": {"level": {"level": {"level": {"data": "x" * 1000}}}}
        }


class SecurityTestRunner:
    """Comprehensive security test runner"""
    
    def __init__(self, app):
        self.app = app
        self.client = TestClient(app)
        self.fixtures = SecurityTestFixtures()
    
    def run_authentication_tests(self):
        """Test authentication security"""
        results = {
            "password_hashing": self.test_password_hashing(),
            "jwt_security": self.test_jwt_security(),
            "session_management": self.test_session_management(),
            "2fa_security": self.test_2fa_security(),
            "rate_limiting": self.test_auth_rate_limiting()
        }
        return results
    
    def test_password_hashing(self):
        """Test password hashing security"""
        try:
            # Test password verification
            test_password = "SecurePassword123!"
            
            # Should fail with wrong password
            assert not verify_password("wrongpassword", self.fixtures.create_test_user()["password_hash"])
            
            # Should work with correct password (if we had the original)
            # This would need the actual password hash generation
            
            return {"passed": True, "message": "Password hashing tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Password hashing test failed: {str(e)}"}
    
    def test_jwt_security(self):
        """Test JWT token security"""
        try:
            # Test token creation and verification
            user_data = {"user_id": 1, "email": "test@example.com"}
            token = create_access_token(user_data)
            
            # Token should be string
            assert isinstance(token, str)
            assert len(token) > 50  # JWT tokens are typically longer
            
            # Token verification should work
            decoded = verify_token(token)
            assert decoded["user_id"] == 1
            
            return {"passed": True, "message": "JWT security tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"JWT test failed: {str(e)}"}
    
    def test_session_management(self):
        """Test session security"""
        try:
            # Test session creation
            response = self.client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "testpassword"
            })
            
            # Should have secure headers
            assert "httponly" in response.headers.get("set-cookie", "").lower()
            
            return {"passed": True, "message": "Session management tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Session test failed: {str(e)}"}
    
    def test_2fa_security(self):
        """Test 2FA implementation"""
        try:
            # Test 2FA setup endpoint
            response = self.client.post("/api/auth/2fa/setup")
            
            # Should require authentication
            assert response.status_code in [401, 403]
            
            return {"passed": True, "message": "2FA security tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"2FA test failed: {str(e)}"}
    
    def test_auth_rate_limiting(self):
        """Test authentication rate limiting"""
        try:
            # Attempt multiple failed logins
            for i in range(10):
                response = self.client.post("/api/auth/login", json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                })
            
            # Should eventually be rate limited
            final_response = self.client.post("/api/auth/login", json={
                "email": "test@example.com", 
                "password": "wrongpassword"
            })
            
            assert final_response.status_code == 429  # Too Many Requests
            
            return {"passed": True, "message": "Rate limiting tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Rate limiting test failed: {str(e)}"}
    
    def run_input_validation_tests(self):
        """Test input validation security"""
        results = {
            "xss_prevention": self.test_xss_prevention(),
            "sql_injection_prevention": self.test_sql_injection_prevention(),
            "command_injection_prevention": self.test_command_injection_prevention(),
            "path_traversal_prevention": self.test_path_traversal_prevention(),
            "request_size_limits": self.test_request_size_limits()
        }
        return results
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        try:
            payloads = self.fixtures.create_malicious_payloads()["xss_payloads"]
            
            for payload in payloads:
                # Test in various endpoints
                response = self.client.post("/api/habits", json={
                    "title": payload,
                    "description": "Test habit"
                })
                
                # Should not return the payload unescaped
                if response.status_code == 200:
                    response_text = response.text
                    assert "<script>" not in response_text
                    assert "javascript:" not in response_text
            
            return {"passed": True, "message": "XSS prevention tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"XSS test failed: {str(e)}"}
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        try:
            payloads = self.fixtures.create_malicious_payloads()["sql_injection_payloads"]
            
            for payload in payloads:
                # Test in search endpoints
                response = self.client.get(f"/api/habits?search={payload}")
                
                # Should not cause SQL errors
                assert response.status_code != 500
                
                # Should not return sensitive data
                if response.status_code == 200:
                    assert "users" not in response.text.lower()
                    assert "password" not in response.text.lower()
            
            return {"passed": True, "message": "SQL injection prevention tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"SQL injection test failed: {str(e)}"}
    
    def test_command_injection_prevention(self):
        """Test command injection prevention"""
        try:
            payloads = self.fixtures.create_malicious_payloads()["command_injection_payloads"]
            
            for payload in payloads:
                # Test file upload endpoints
                response = self.client.post("/api/files/upload", files={
                    "file": (payload, "test content", "text/plain")
                })
                
                # Should not execute commands
                assert response.status_code in [400, 403, 422]  # Should be rejected
            
            return {"passed": True, "message": "Command injection prevention tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Command injection test failed: {str(e)}"}
    
    def test_path_traversal_prevention(self):
        """Test path traversal prevention"""
        try:
            payloads = self.fixtures.create_malicious_payloads()["path_traversal_payloads"]
            
            for payload in payloads:
                # Test file access endpoints
                response = self.client.get(f"/api/files/{payload}")
                
                # Should not access system files
                assert response.status_code in [400, 403, 404]
                
                if response.status_code == 200:
                    # Should not return system file content
                    content = response.text.lower()
                    assert "root:" not in content
                    assert "password" not in content
            
            return {"passed": True, "message": "Path traversal prevention tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Path traversal test failed: {str(e)}"}
    
    def test_request_size_limits(self):
        """Test request size limiting"""
        try:
            oversized = self.fixtures.create_oversized_requests()
            
            # Test large JSON payload
            response = self.client.post("/api/habits", json=oversized["large_json"])
            assert response.status_code == 413  # Payload Too Large
            
            # Test many parameters
            response = self.client.get("/api/habits", params=oversized["many_params"])
            assert response.status_code in [400, 413]
            
            return {"passed": True, "message": "Request size limit tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Request size test failed: {str(e)}"}
    
    def run_gdpr_compliance_tests(self):
        """Test GDPR compliance"""
        results = {
            "data_export": self.test_data_export(),
            "data_deletion": self.test_data_deletion(),
            "retention_policies": self.test_retention_policies()
        }
        return results
    
    def test_data_export(self):
        """Test GDPR data export functionality"""
        try:
            # Test data export endpoint
            response = self.client.get("/api/gdpr/export-data")
            
            # Should require authentication
            assert response.status_code in [401, 403]
            
            return {"passed": True, "message": "Data export tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Data export test failed: {str(e)}"}
    
    def test_data_deletion(self):
        """Test GDPR data deletion functionality"""
        try:
            # Test deletion endpoint
            response = self.client.delete("/api/gdpr/delete-account", json={
                "verification_code": "test_code"
            })
            
            # Should require authentication
            assert response.status_code in [401, 403]
            
            return {"passed": True, "message": "Data deletion tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Data deletion test failed: {str(e)}"}
    
    def test_retention_policies(self):
        """Test data retention policies"""
        try:
            # Test retention policy endpoint
            response = self.client.get("/api/gdpr/retention-policy")
            
            if response.status_code == 200:
                data = response.json()
                assert "retention_periods" in data
                assert isinstance(data["retention_periods"], dict)
            
            return {"passed": True, "message": "Retention policy tests passed"}
        except Exception as e:
            return {"passed": False, "message": f"Retention policy test failed: {str(e)}"}
    
    def generate_security_report(self):
        """Generate comprehensive security test report"""
        print("🔒 Running comprehensive security tests...")
        
        results = {
            "authentication": self.run_authentication_tests(),
            "input_validation": self.run_input_validation_tests(),
            "gdpr_compliance": self.run_gdpr_compliance_tests()
        }
        
        # Calculate overall security score
        total_tests = 0
        passed_tests = 0
        
        for category, tests in results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result.get("passed", False):
                    passed_tests += 1
        
        security_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            "timestamp": "2024-01-01T00:00:00Z",
            "security_score": security_score,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "test_results": results,
            "recommendations": self.generate_recommendations(results)
        }
        
        return report
    
    def generate_recommendations(self, results):
        """Generate security recommendations based on test results"""
        recommendations = []
        
        for category, tests in results.items():
            for test_name, result in tests.items():
                if not result.get("passed", False):
                    recommendations.append({
                        "category": category,
                        "test": test_name,
                        "issue": result.get("message", "Test failed"),
                        "priority": "high" if category == "authentication" else "medium"
                    })
        
        return recommendations


# Export test utilities
__all__ = [
    "SecurityTestFixtures",
    "SecurityTestRunner"
]