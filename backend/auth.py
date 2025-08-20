"""
Matrica Networks - Authentication Module
Handles user authentication, session management, and security
"""

import hashlib
import hmac
import secrets
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import sqlite3
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration constants"""
    # Password hashing
    HASH_ALGORITHM = 'sha256'
    HASH_ITERATIONS = 100000
    SALT_LENGTH = 32
    
    # Session management
    SESSION_TOKEN_LENGTH = 64
    SESSION_EXPIRY_HOURS = 8
    SESSION_REMEMBER_HOURS = 168  # 7 days
    
    # Rate limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    # Security headers
    SECURE_HEADERS = {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    }

class RateLimiter:
    """Handle rate limiting for authentication attempts"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_rate_limit_table()
    
    def _init_rate_limit_table(self):
        """Initialize rate limiting table"""
        with self._get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    identifier TEXT PRIMARY KEY,
                    attempts INTEGER DEFAULT 0,
                    first_attempt TIMESTAMP,
                    last_attempt TIMESTAMP,
                    locked_until TIMESTAMP
                )
            ''')
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def check_rate_limit(self, identifier: str) -> Dict[str, Any]:
        """Check if identifier is rate limited"""
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM rate_limits WHERE identifier = ?
            ''', (identifier,))
            
            record = cursor.fetchone()
            current_time = datetime.now()
            
            if not record:
                return {'allowed': True, 'attempts': 0}
            
            # Check if lockout period has expired
            if record['locked_until'] and datetime.fromisoformat(record['locked_until']) > current_time:
                time_remaining = datetime.fromisoformat(record['locked_until']) - current_time
                return {
                    'allowed': False,
                    'attempts': record['attempts'],
                    'locked_until': record['locked_until'],
                    'time_remaining_minutes': int(time_remaining.total_seconds() / 60)
                }
            
            # Reset if lockout expired
            if record['locked_until'] and datetime.fromisoformat(record['locked_until']) <= current_time:
                conn.execute('''
                    UPDATE rate_limits 
                    SET attempts = 0, first_attempt = NULL, last_attempt = NULL, locked_until = NULL
                    WHERE identifier = ?
                ''', (identifier,))
                conn.commit()
                return {'allowed': True, 'attempts': 0}
            
            return {'allowed': record['attempts'] < SecurityConfig.MAX_LOGIN_ATTEMPTS, 'attempts': record['attempts']}
    
    def record_attempt(self, identifier: str, success: bool = False):
        """Record a login attempt"""
        current_time = datetime.now()
        
        with self._get_db_connection() as conn:
            if success:
                # Reset on successful login
                conn.execute('DELETE FROM rate_limits WHERE identifier = ?', (identifier,))
            else:
                # Increment failed attempts
                cursor = conn.execute('SELECT * FROM rate_limits WHERE identifier = ?', (identifier,))
                record = cursor.fetchone()
                
                if record:
                    new_attempts = record['attempts'] + 1
                    locked_until = None
                    
                    if new_attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                        locked_until = (current_time + timedelta(minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES)).isoformat()
                    
                    conn.execute('''
                        UPDATE rate_limits 
                        SET attempts = ?, last_attempt = ?, locked_until = ?
                        WHERE identifier = ?
                    ''', (new_attempts, current_time.isoformat(), locked_until, identifier))
                else:
                    conn.execute('''
                        INSERT INTO rate_limits (identifier, attempts, first_attempt, last_attempt)
                        VALUES (?, 1, ?, ?)
                    ''', (identifier, current_time.isoformat(), current_time.isoformat()))
            
            conn.commit()

class PasswordPolicy:
    """Password policy enforcement"""
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password against policy"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for common passwords (simplified check)
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': PasswordPolicy._calculate_strength(password)
        }
    
    @staticmethod
    def _calculate_strength(password: str) -> str:
        """Calculate password strength"""
        score = 0
        
        # Length bonus
        score += min(len(password), 25)
        
        # Character variety
        if any(c.isupper() for c in password):
            score += 6
        if any(c.islower() for c in password):
            score += 6
        if any(c.isdigit() for c in password):
            score += 6
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 6
        
        # Patterns penalty
        if password.lower() in password or password.upper() in password:
            score -= 10
        
        if score < 20:
            return 'weak'
        elif score < 35:
            return 'medium'
        else:
            return 'strong'

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_audit_table()
    
    def _init_audit_table(self):
        """Initialize audit log table"""
        with self._get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    username TEXT,
                    client_ip TEXT,
                    user_agent TEXT,
                    details TEXT,
                    success BOOLEAN
                )
            ''')
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def log_event(self, event_type: str, user_id: int = None, username: str = None, 
                  client_ip: str = None, user_agent: str = None, details: Dict = None, success: bool = True):
        """Log security event"""
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO audit_logs (event_type, user_id, username, client_ip, user_agent, details, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_type, 
                    user_id, 
                    username, 
                    client_ip, 
                    user_agent, 
                    json.dumps(details) if details else None,
                    success
                ))
                conn.commit()
                
            logger.info(f"Audit: {event_type} - User: {username} - Success: {success}")
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

class AuthService:
    """Main authentication service"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.rate_limiter = RateLimiter(db_path)
        self.audit_logger = AuditLogger(db_path)
        self._init_auth_tables()
    
    def _init_auth_tables(self):
        """Initialize authentication tables"""
        with self._get_db_connection() as conn:
            # Sessions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    client_ip TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create index for faster session lookups
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token)
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _hash_password(self, password: str, salt: bytes = None) -> tuple:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(SecurityConfig.SALT_LENGTH)
        
        password_hash = hashlib.pbkdf2_hmac(
            SecurityConfig.HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            SecurityConfig.HASH_ITERATIONS
        )
        
        return password_hash, salt
    
    def _verify_password(self, password: str, stored_hash: bytes, salt: bytes) -> bool:
        """Verify password against stored hash"""
        password_hash, _ = self._hash_password(password, salt)
        return hmac.compare_digest(password_hash, stored_hash)
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(SecurityConfig.SESSION_TOKEN_LENGTH)
    
    def authenticate_user(self, username: str, password: str, client_ip: str = None, user_agent: str = None) -> Optional[Dict]:
        """Authenticate user with username/password"""
        # Check rate limiting
        rate_limit_result = self.rate_limiter.check_rate_limit(username)
        if not rate_limit_result['allowed']:
            self.audit_logger.log_event('login_blocked', username=username, client_ip=client_ip, 
                                      user_agent=user_agent, details={'reason': 'rate_limited'}, success=False)
            return None
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute('''
                    SELECT id, username, password_hash, salt, role, is_active 
                    FROM users WHERE username = ? OR email = ?
                ''', (username, username))
                
                user = cursor.fetchone()
                
                if not user:
                    self.rate_limiter.record_attempt(username, success=False)
                    self.audit_logger.log_event('login_failed', username=username, client_ip=client_ip,
                                              user_agent=user_agent, details={'reason': 'user_not_found'}, success=False)
                    return None
                
                if not user['is_active']:
                    self.rate_limiter.record_attempt(username, success=False)
                    self.audit_logger.log_event('login_failed', user_id=user['id'], username=username, 
                                              client_ip=client_ip, user_agent=user_agent, 
                                              details={'reason': 'account_disabled'}, success=False)
                    return None
                
                # Verify password
                stored_hash = user['password_hash']
                salt = user['salt']
                
                if isinstance(stored_hash, str):
                    stored_hash = bytes.fromhex(stored_hash)
                if isinstance(salt, str):
                    salt = bytes.fromhex(salt)
                
                if not self._verify_password(password, stored_hash, salt):
                    self.rate_limiter.record_attempt(username, success=False)
                    self.audit_logger.log_event('login_failed', user_id=user['id'], username=username, 
                                              client_ip=client_ip, user_agent=user_agent, 
                                              details={'reason': 'invalid_password'}, success=False)
                    return None
                
                # Success
                self.rate_limiter.record_attempt(username, success=True)
                self.audit_logger.log_event('login_success', user_id=user['id'], username=username, 
                                          client_ip=client_ip, user_agent=user_agent, success=True)
                
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.audit_logger.log_event('login_error', username=username, client_ip=client_ip,
                                      user_agent=user_agent, details={'error': str(e)}, success=False)
            return None
    
    def create_session(self, user_id: int, client_ip: str = None, user_agent: str = None, remember: bool = False) -> Optional[str]:
        """Create new user session"""
        try:
            session_token = self._generate_session_token()
            expires_hours = SecurityConfig.SESSION_REMEMBER_HOURS if remember else SecurityConfig.SESSION_EXPIRY_HOURS
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO user_sessions (user_id, session_token, expires_at, client_ip, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, session_token, expires_at.isoformat(), client_ip, user_agent))
                conn.commit()
            
            self.audit_logger.log_event('session_created', user_id=user_id, client_ip=client_ip,
                                      user_agent=user_agent, details={'remember': remember}, success=True)
            
            return session_token
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user info"""
        if not session_token:
            return None
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute('''
                    SELECT s.*, u.username, u.role, u.is_active
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.is_active = 1
                ''', (session_token,))
                
                session = cursor.fetchone()
                
                if not session:
                    return None
                
                # Check if session expired
                expires_at = datetime.fromisoformat(session['expires_at'])
                if expires_at < datetime.now():
                    # Deactivate expired session
                    conn.execute('''
                        UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
                    ''', (session_token,))
                    conn.commit()
                    
                    self.audit_logger.log_event('session_expired', user_id=session['user_id'], 
                                              details={'session_token': session_token[:16] + '...'}, success=False)
                    return None
                
                # Check if user is still active
                if not session['is_active']:
                    return None
                
                return {
                    'id': session['user_id'],
                    'username': session['username'],
                    'role': session['role'],
                    'session_created': session['created_at'],
                    'session_expires': session['expires_at']
                }
                
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def logout_session(self, session_token: str) -> bool:
        """Logout session (deactivate)"""
        if not session_token:
            return False
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute('''
                    SELECT user_id FROM user_sessions WHERE session_token = ? AND is_active = 1
                ''', (session_token,))
                session = cursor.fetchone()
                
                if session:
                    conn.execute('''
                        UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
                    ''', (session_token,))
                    conn.commit()
                    
                    self.audit_logger.log_event('logout', user_id=session['user_id'], 
                                              details={'session_token': session_token[:16] + '...'}, success=True)
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (should be run periodically)"""
        try:
            with self._get_db_connection() as conn:
                current_time = datetime.now().isoformat()
                cursor = conn.execute('''
                    UPDATE user_sessions 
                    SET is_active = 0 
                    WHERE expires_at < ? AND is_active = 1
                ''', (current_time,))
                
                cleaned_count = cursor.rowcount
                conn.commit()
                
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    def change_password(self, user_id: int, current_password: str, new_password: str, client_ip: str = None) -> Dict[str, Any]:
        """Change user password"""
        # Validate new password
        password_validation = PasswordPolicy.validate_password(new_password)
        if not password_validation['valid']:
            return {
                'success': False,
                'error': 'invalid_password',
                'details': password_validation['errors']
            }
        
        try:
            with self._get_db_connection() as conn:
                # Get current user
                cursor = conn.execute('''
                    SELECT username, password_hash, salt FROM users WHERE id = ?
                ''', (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return {'success': False, 'error': 'user_not_found'}
                
                # Verify current password
                stored_hash = bytes.fromhex(user['password_hash']) if isinstance(user['password_hash'], str) else user['password_hash']
                salt = bytes.fromhex(user['salt']) if isinstance(user['salt'], str) else user['salt']
                
                if not self._verify_password(current_password, stored_hash, salt):
                    self.audit_logger.log_event('password_change_failed', user_id=user_id, 
                                              username=user['username'], client_ip=client_ip,
                                              details={'reason': 'invalid_current_password'}, success=False)
                    return {'success': False, 'error': 'invalid_current_password'}
                
                # Hash new password
                new_hash, new_salt = self._hash_password(new_password)
                
                # Update password
                conn.execute('''
                    UPDATE users 
                    SET password_hash = ?, salt = ?, password_changed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_hash.hex(), new_salt.hex(), user_id))
                conn.commit()
                
                # Invalidate all existing sessions for security
                conn.execute('''
                    UPDATE user_sessions SET is_active = 0 WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                
                self.audit_logger.log_event('password_changed', user_id=user_id, 
                                          username=user['username'], client_ip=client_ip, success=True)
                
                return {'success': True}
                
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return {'success': False, 'error': 'internal_error'}

# Initialize global auth service (will be imported by other modules)
auth_service = None

def init_auth_service(db_path: str):
    """Initialize the global auth service"""
    global auth_service
    auth_service = AuthService(db_path)
    return auth_service

def get_auth_service() -> AuthService:
    """Get the global auth service instance"""
    return auth_service