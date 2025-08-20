#!/usr/bin/env python3
"""
Matrica Networks - Security & Authentication Middleware
Comprehensive security layers for the WSGI application
"""

import os
import re
import json
import logging
from typing import Dict, Optional, Tuple, Any, List
from urllib.parse import parse_qs
from models import Session, User, AuditLog
from auth import get_auth_service

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for request validation and protection"""
    
    def __init__(self):
        # Security patterns
        self.sql_injection_patterns = [
            r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(\-\-|\#|\/\*|\*\/)",
            r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
            r"(\'\s*(OR|AND)\s+\'\w+\'\s*=\s*\'\w+\')"
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>"
        ]
        
        self.file_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"/etc/passwd",
            r"/proc/",
            r"\\windows\\",
            r"\\system32\\"
        ]
        
        # Blocked user agents (bots, scanners)
        self.blocked_user_agents = [
            r".*sqlmap.*",
            r".*nikto.*",
            r".*nessus.*",
            r".*masscan.*",
            r".*nmap.*",
            r".*w3af.*",
            r".*burp.*",
            r".*acunetix.*"
        ]
        
        logger.info("Security middleware initialized")
    
    def process_request(self, environ: Dict) -> Optional[Tuple[int, Dict]]:
        """Process request for security threats"""
        try:
            # Get request information
            method = environ.get('REQUEST_METHOD', '')
            path = environ.get('PATH_INFO', '')
            query_string = environ.get('QUERY_STRING', '')
            user_agent = environ.get('HTTP_USER_AGENT', '')
            client_ip = environ.get('REMOTE_ADDR', 'unknown')
            
            # Check for blocked user agents
            for pattern in self.blocked_user_agents:
                if re.search(pattern, user_agent, re.IGNORECASE):
                    logger.warning(f"Blocked user agent from {client_ip}: {user_agent}")
                    return (403, {'error': 'Forbidden'})
            
            # Check path for security threats
            security_check = self._check_security_threats(path + '?' + query_string)
            if security_check:
                logger.warning(f"Security threat detected from {client_ip}: {security_check}")
                AuditLog.log(
                    user_id=None,
                    action='SECURITY_THREAT',
                    details=f"Threat: {security_check}, Path: {path}",
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                return (403, {'error': 'Security threat detected'})
            
            # Check request body for POST/PUT
            if method in ['POST', 'PUT']:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    # Read body without consuming the stream
                    body = environ['wsgi.input'].read(content_length)
                    environ['wsgi.input'] = self._wrap_input(body)
                    
                    try:
                        body_str = body.decode('utf-8')
                        security_check = self._check_security_threats(body_str)
                        if security_check:
                            logger.warning(f"Security threat in request body from {client_ip}: {security_check}")
                            return (403, {'error': 'Security threat detected in request body'})
                    except UnicodeDecodeError:
                        # Binary data, skip security check
                        pass
            
            # All checks passed
            return None
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            return (500, {'error': 'Security check failed'})
    
    def _check_security_threats(self, content: str) -> Optional[str]:
        """Check content for various security threats"""
        content_lower = content.lower()
        
        # SQL Injection detection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return "SQL Injection attempt"
        
        # XSS detection
        for pattern in self.xss_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return "XSS attempt"
        
        # File traversal detection
        for pattern in self.file_traversal_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return "File traversal attempt"
        
        # Check for common attack patterns
        attack_patterns = [
            r"<\?php",
            r"eval\s*\(",
            r"system\s*\(",
            r"exec\s*\(",
            r"shell_exec\s*\(",
            r"passthru\s*\(",
            r"base64_decode\s*\(",
            r"gzinflate\s*\(",
            r"<!--#exec",
            r"<%.*%>",
            r"\${.*}",
            r"{{.*}}"
        ]
        
        for pattern in attack_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return "Code injection attempt"
        
        return None
    
    def _wrap_input(self, body: bytes):
        """Wrap body bytes in a file-like object"""
        from io import BytesIO
        return BytesIO(body)

class AuthMiddleware:
    """Authentication middleware for session management"""
    
    def __init__(self):
        self.session_cookie_name = 'session_token'
        logger.info("Authentication middleware initialized")
    
    def process_request(self, environ: Dict) -> Optional[Dict]:
        """Process request for authentication"""
        try:
            # Get session cookie
            cookie_header = environ.get('HTTP_COOKIE', '')
            session_token = self._extract_session_token(cookie_header)
            
            if not session_token:
                return (401, {'error': 'Authentication required'})
            
            # Get auth service
            auth_service = get_auth_service()
            if not auth_service:
                return (500, {'error': 'Authentication service unavailable'})
            
            # Validate session
            user = auth_service.validate_session(session_token)
            if not user:
                return (401, {'error': 'Invalid or expired session'})
            
            # Return session context
            return {
                'session_token': session_token,
                'user': user
            }
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {str(e)}")
            return (500, {'error': 'Authentication check failed'})
    
    def _extract_session_token(self, cookie_header: str) -> Optional[str]:
        """Extract session token from cookie header"""
        if not cookie_header:
            return None
        
        # Parse cookies
        cookies = {}
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookies[name] = value
        
        return cookies.get(self.session_cookie_name)

class InputValidationMiddleware:
    """Input validation and sanitization middleware"""
    
    def __init__(self):
        # Define validation rules for different input types
        self.validation_rules = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[\d\s\-\(\)]{10,15}$',
            'username': r'^[a-zA-Z0-9._-]{3,20}$',
            'password': r'^.{8,128}$',  # Min 8 chars, max 128
            'name': r'^[a-zA-Z\s]{2,50}$',
            'safe_text': r'^[a-zA-Z0-9\s.,!?-]{1,500}$'
        }
        
        logger.info("Input validation middleware initialized")
    
    def validate_input(self, data: Dict, rules: Dict) -> Tuple[bool, Dict]:
        """Validate input data against rules"""
        errors = {}
        
        for field, rule_type in rules.items():
            if field not in data:
                if rule_type.endswith('_required'):
                    errors[field] = f"{field} is required"
                continue
            
            value = data[field]
            rule_type = rule_type.replace('_required', '')
            
            if rule_type in self.validation_rules:
                pattern = self.validation_rules[rule_type]
                if not re.match(pattern, str(value)):
                    errors[field] = f"Invalid {field} format"
        
        return len(errors) == 0, errors
    
    def sanitize_input(self, data: Dict) -> Dict:
        """Sanitize input data"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                value = re.sub(r'[<>"\'\\\x00-\x1f\x7f-\x9f]', '', value)
                # Trim whitespace
                value = value.strip()
                # Limit length
                value = value[:1000] if len(value) > 1000 else value
            
            sanitized[key] = value
        
        return sanitized

class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self):
        # Rate limit configurations (requests per window)
        self.rate_limits = {
            '/api/auth/login': {'requests': 5, 'window': 15},  # 5 attempts per 15 minutes
            '/api/contact': {'requests': 3, 'window': 10},     # 3 submissions per 10 minutes
            '/api/': {'requests': 100, 'window': 15},          # 100 API calls per 15 minutes
            'default': {'requests': 200, 'window': 15}         # Default limit
        }
        
        logger.info("Rate limiting middleware initialized")
    
    def check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """Check if request is within rate limits"""
        try:
            # Find applicable rate limit
            config = None
            for pattern, limit_config in self.rate_limits.items():
                if endpoint.startswith(pattern):
                    config = limit_config
                    break
            
            if not config:
                config = self.rate_limits['default']
            
            # Check rate limit using the model
            from models import RateLimit
            return RateLimit.check_rate_limit(
                client_ip, 
                endpoint, 
                config['requests'], 
                config['window']
            )
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True  # Allow request on error

class CORSMiddleware:
    """CORS middleware for cross-origin requests"""
    
    def __init__(self):
        self.allowed_origins = ['http://localhost:8000']
        self.allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.allowed_headers = ['Content-Type', 'Authorization', 'X-CSRF-Token']
        logger.info("CORS middleware initialized")
    
    def process_request(self, environ: Dict) -> Optional[Tuple[int, Dict, List]]:
        """Process CORS headers"""
        origin = environ.get('HTTP_ORIGIN', '')
        method = environ.get('REQUEST_METHOD', '')
        
        # Handle preflight requests
        if method == 'OPTIONS':
            headers = [
                ('Access-Control-Allow-Origin', origin if origin in self.allowed_origins else ''),
                ('Access-Control-Allow-Methods', ', '.join(self.allowed_methods)),
                ('Access-Control-Allow-Headers', ', '.join(self.allowed_headers)),
                ('Access-Control-Max-Age', '86400')
            ]
            return (200, {}, headers)
        
        return None
    
    def add_cors_headers(self, headers: List, environ: Dict) -> List:
        """Add CORS headers to response"""
        origin = environ.get('HTTP_ORIGIN', '')
        
        if origin in self.allowed_origins:
            headers.append(('Access-Control-Allow-Origin', origin))
            headers.append(('Access-Control-Allow-Credentials', 'true'))
        
        return headers