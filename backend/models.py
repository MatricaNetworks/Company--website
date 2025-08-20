#!/usr/bin/env python3
"""
Matrica Networks - Database Models
Clean, secure data access layer with prepared statements
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), 'matrica.db')

class Database:
    """Database connection manager with security features"""
    
    @staticmethod
    def get_connection():
        """Get database connection with security settings"""
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable FK constraints
        return conn
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: str = None):
        """Safely execute query with prepared statements"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch == 'one':
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch == 'all':
                results = cursor.fetchall()
                return [dict(row) for row in results]
            elif fetch == 'lastrowid':
                conn.commit()
                return cursor.lastrowid
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class User:
    """User model with authentication methods"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Hash password with PBKDF2 and salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username/password"""
        user = Database.execute_query(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
            'one'
        )
        
        if not user:
            return None
        
        # Verify password
        password_hash, _ = User.hash_password(password, user['salt'])
        if password_hash == user['password_hash']:
            # Update last login
            Database.execute_query(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user['id'])
            )
            return user
        
        return None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return Database.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
            'one'
        )
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all users"""
        return Database.execute_query(
            "SELECT * FROM users ORDER BY created_at DESC",
            fetch='all'
        )
    
    @staticmethod
    def create(data: Dict) -> int:
        """Create new user"""
        password_hash, salt = User.hash_password(data['password'])
        
        return Database.execute_query('''
            INSERT INTO users (
                username, email, password_hash, salt, first_name, last_name,
                role, employee_id, department, designation, phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'], data['email'], password_hash, salt,
            data['first_name'], data['last_name'], data.get('role', 'employee'),
            data.get('employee_id'), data.get('department'), 
            data.get('designation'), data.get('phone')
        ), 'lastrowid')
    
    @staticmethod
    def update(user_id: int, data: Dict) -> int:
        """Update user"""
        # Build dynamic query based on provided data
        fields = []
        values = []
        
        for field in ['first_name', 'last_name', 'email', 'department', 'designation', 'phone']:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])
        
        if 'password' in data:
            password_hash, salt = User.hash_password(data['password'])
            fields.extend(['password_hash = ?', 'salt = ?'])
            values.extend([password_hash, salt])
        
        fields.append('updated_at = ?')
        values.append(datetime.now())
        values.append(user_id)
        
        return Database.execute_query(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
            tuple(values)
        )
    
    @staticmethod
    def delete(user_id: int) -> int:
        """Soft delete user"""
        return Database.execute_query(
            "UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now(), user_id)
        )

class Session:
    """Session management for secure authentication"""
    
    @staticmethod
    def create(user_id: int, ip_address: str = None, user_agent: str = None) -> tuple:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        Database.execute_query('''
            INSERT INTO sessions (id, user_id, csrf_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, csrf_token, expires_at, ip_address, user_agent))
        
        return session_id, csrf_token
    
    @staticmethod
    def get(session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        session = Database.execute_query(
            "SELECT * FROM sessions WHERE id = ? AND expires_at > ?",
            (session_id, datetime.now()),
            'one'
        )
        
        if session:
            # Update last accessed
            Database.execute_query(
                "UPDATE sessions SET last_accessed = ? WHERE id = ?",
                (datetime.now(), session_id)
            )
        
        return session
    
    @staticmethod
    def delete(session_id: str) -> int:
        """Delete session (logout)"""
        return Database.execute_query(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )
    
    @staticmethod
    def cleanup_expired() -> int:
        """Clean up expired sessions"""
        return Database.execute_query(
            "DELETE FROM sessions WHERE expires_at < ?",
            (datetime.now(),)
        )

class Project:
    """Project management model"""
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all projects with manager info"""
        return Database.execute_query('''
            SELECT p.*, u.first_name || ' ' || u.last_name as manager_name
            FROM projects p
            LEFT JOIN users u ON p.manager_id = u.id
            ORDER BY p.created_at DESC
        ''', fetch='all')
    
    @staticmethod
    def get_by_id(project_id: int) -> Optional[Dict]:
        """Get project by ID"""
        return Database.execute_query(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
            'one'
        )
    
    @staticmethod
    def create(data: Dict) -> int:
        """Create new project"""
        return Database.execute_query('''
            INSERT INTO projects (
                name, description, status, priority, start_date, end_date, 
                deadline, manager_id, client_name, budget
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], data.get('description'), data.get('status', 'planning'),
            data.get('priority', 'medium'), data.get('start_date'), 
            data.get('end_date'), data.get('deadline'), data.get('manager_id'),
            data.get('client_name'), data.get('budget')
        ), 'lastrowid')
    
    @staticmethod
    def update(project_id: int, data: Dict) -> int:
        """Update project"""
        fields = []
        values = []
        
        for field in ['name', 'description', 'status', 'priority', 'start_date', 
                     'end_date', 'deadline', 'manager_id', 'client_name', 'budget']:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])
        
        fields.append('updated_at = ?')
        values.append(datetime.now())
        values.append(project_id)
        
        return Database.execute_query(
            f"UPDATE projects SET {', '.join(fields)} WHERE id = ?",
            tuple(values)
        )
    
    @staticmethod
    def delete(project_id: int) -> int:
        """Delete project"""
        return Database.execute_query(
            "DELETE FROM projects WHERE id = ?",
            (project_id,)
        )

class Task:
    """Task management model"""
    
    @staticmethod
    def get_by_user(user_id: int) -> List[Dict]:
        """Get tasks assigned to user"""
        return Database.execute_query('''
            SELECT t.*, p.name as project_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.assigned_to = ?
            ORDER BY t.due_date ASC, t.priority DESC
        ''', (user_id,), 'all')
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all tasks with project and assignee info"""
        return Database.execute_query('''
            SELECT t.*, p.name as project_name, 
                   u.first_name || ' ' || u.last_name as assignee_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u ON t.assigned_to = u.id
            ORDER BY t.created_at DESC
        ''', fetch='all')
    
    @staticmethod
    def create(data: Dict) -> int:
        """Create new task"""
        return Database.execute_query('''
            INSERT INTO tasks (
                project_id, title, description, status, priority,
                assigned_to, assigned_by, estimated_hours, start_date, due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('project_id'), data['title'], data.get('description'),
            data.get('status', 'todo'), data.get('priority', 'medium'),
            data.get('assigned_to'), data.get('assigned_by'), 
            data.get('estimated_hours'), data.get('start_date'), data.get('due_date')
        ), 'lastrowid')

class Blog:
    """Blog management model"""
    
    @staticmethod
    def get_published(blog_type: str = None) -> List[Dict]:
        """Get published blogs by type"""
        if blog_type:
            return Database.execute_query('''
                SELECT b.*, u.first_name || ' ' || u.last_name as author_name
                FROM blogs b
                JOIN users u ON b.author_id = u.id
                WHERE b.status = 'published' AND b.type = ?
                ORDER BY b.published_at DESC
            ''', (blog_type,), 'all')
        else:
            return Database.execute_query('''
                SELECT b.*, u.first_name || ' ' || u.last_name as author_name
                FROM blogs b
                JOIN users u ON b.author_id = u.id
                WHERE b.status = 'published'
                ORDER BY b.published_at DESC
            ''', fetch='all')
    
    @staticmethod
    def get_by_id(blog_id: int) -> Optional[Dict]:
        """Get blog by ID with author info"""
        return Database.execute_query('''
            SELECT b.*, u.first_name || ' ' || u.last_name as author_name
            FROM blogs b
            JOIN users u ON b.author_id = u.id
            WHERE b.id = ?
        ''', (blog_id,), 'one')
    
    @staticmethod
    def create(data: Dict) -> int:
        """Create new blog entry"""
        published_at = datetime.now() if data.get('status') == 'published' else None
        
        return Database.execute_query('''
            INSERT INTO blogs (
                title, type, content, excerpt, author_id, cover_image_path,
                status, tags, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'], data['type'], data['content'], data.get('excerpt'),
            data['author_id'], data.get('cover_image_path'), 
            data.get('status', 'draft'), data.get('tags'), published_at
        ), 'lastrowid')
    
    @staticmethod
    def update(blog_id: int, data: Dict) -> int:
        """Update blog entry"""
        fields = []
        values = []
        
        for field in ['title', 'type', 'content', 'excerpt', 'cover_image_path', 'status', 'tags']:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])
        
        if 'status' in data and data['status'] == 'published':
            fields.append('published_at = ?')
            values.append(datetime.now())
        
        fields.append('updated_at = ?')
        values.append(datetime.now())
        values.append(blog_id)
        
        return Database.execute_query(
            f"UPDATE blogs SET {', '.join(fields)} WHERE id = ?",
            tuple(values)
        )
    
    @staticmethod
    def delete(blog_id: int) -> int:
        """Delete blog entry"""
        return Database.execute_query(
            "DELETE FROM blogs WHERE id = ?",
            (blog_id,)
        )

class Contact:
    """Contact inquiry model"""
    
    @staticmethod
    def create(data: Dict) -> int:
        """Create contact inquiry"""
        return Database.execute_query('''
            INSERT INTO contact_inquiries (name, organization, email, phone, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['name'], data.get('organization'), data['email'],
            data.get('phone'), data['reason']
        ), 'lastrowid')
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all contact inquiries"""
        return Database.execute_query(
            "SELECT * FROM contact_inquiries ORDER BY created_at DESC",
            fetch='all'
        )

class AuditLog:
    """Security audit logging"""
    
    @staticmethod
    def log(user_id: int, action: str, resource_type: str = None, 
            resource_id: str = None, details: str = None,
            ip_address: str = None, user_agent: str = None):
        """Log security event"""
        Database.execute_query('''
            INSERT INTO audit_log (
                user_id, action, resource_type, resource_id, details,
                ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action, resource_type, resource_id, details, ip_address, user_agent))
    
    @staticmethod
    def get_recent(limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        return Database.execute_query('''
            SELECT a.*, u.username
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT ?
        ''', (limit,), 'all')

class RateLimit:
    """Rate limiting for API endpoints"""
    
    @staticmethod
    def check_rate_limit(ip_address: str, endpoint: str, max_requests: int = 100, 
                        window_minutes: int = 15) -> bool:
        """Check if request is within rate limit"""
        window_start = datetime.now() - timedelta(minutes=window_minutes)
        
        # Get current request count
        current = Database.execute_query('''
            SELECT requests FROM rate_limits 
            WHERE ip_address = ? AND endpoint = ? AND window_start > ?
        ''', (ip_address, endpoint, window_start), 'one')
        
        if not current:
            # First request in window
            Database.execute_query('''
                INSERT OR REPLACE INTO rate_limits (ip_address, endpoint, requests, window_start)
                VALUES (?, ?, 1, ?)
            ''', (ip_address, endpoint, datetime.now()))
            return True
        
        if current['requests'] >= max_requests:
            return False
        
        # Increment request count
        Database.execute_query('''
            UPDATE rate_limits SET requests = requests + 1
            WHERE ip_address = ? AND endpoint = ?
        ''', (ip_address, endpoint))
        
        return True

class Job:
    """Job posting management model"""
    
    @staticmethod
    def get_published() -> List[Dict]:
        """Get all published job postings"""
        return Database.execute_query('''
            SELECT j.*, u.first_name || ' ' || u.last_name as posted_by_name
            FROM jobs j
            LEFT JOIN users u ON j.posted_by = u.id
            WHERE j.status = 'published'
            ORDER BY j.published_at DESC
        ''', fetch='all')
    
    @staticmethod
    def get_by_filters(department: str = None, location: str = None, 
                      job_type: str = None, experience_level: str = None) -> List[Dict]:
        """Get published jobs with filters"""
        query = '''
            SELECT j.*, u.first_name || ' ' || u.last_name as posted_by_name
            FROM jobs j
            LEFT JOIN users u ON j.posted_by = u.id
            WHERE j.status = 'published'
        '''
        params = []
        
        if department:
            query += " AND j.department = ?"
            params.append(department)
        if location:
            query += " AND j.location LIKE ?"
            params.append(f"%{location}%")
        if job_type:
            query += " AND j.job_type = ?"
            params.append(job_type)
        if experience_level:
            query += " AND j.experience_level = ?"
            params.append(experience_level)
        
        query += " ORDER BY j.published_at DESC"
        
        return Database.execute_query(query, tuple(params), 'all')
    
    @staticmethod
    def get_by_id(job_id: int) -> Optional[Dict]:
        """Get job by ID with poster info"""
        return Database.execute_query('''
            SELECT j.*, u.first_name || ' ' || u.last_name as posted_by_name
            FROM jobs j
            LEFT JOIN users u ON j.posted_by = u.id
            WHERE j.id = ?
        ''', (job_id,), 'one')
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all jobs (admin view)"""
        return Database.execute_query('''
            SELECT j.*, u.first_name || ' ' || u.last_name as posted_by_name
            FROM jobs j
            LEFT JOIN users u ON j.posted_by = u.id
            ORDER BY j.created_at DESC
        ''', fetch='all')
    
    @staticmethod
    def create(data: Dict) -> int:
        """Create new job posting"""
        published_at = datetime.now() if data.get('status') == 'published' else None
        
        return Database.execute_query('''
            INSERT INTO jobs (
                title, department, location, job_type, experience_level,
                description, requirements, responsibilities, benefits,
                salary_min, salary_max, application_deadline, status,
                posted_by, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'], data['department'], data['location'],
            data.get('job_type', 'full-time'), data.get('experience_level', 'mid'),
            data['description'], data.get('requirements'), data.get('responsibilities'),
            data.get('benefits'), data.get('salary_min'), data.get('salary_max'),
            data.get('application_deadline'), data.get('status', 'draft'),
            data['posted_by'], published_at
        ), 'lastrowid')
    
    @staticmethod
    def update(job_id: int, data: Dict) -> int:
        """Update job posting"""
        fields = []
        values = []
        
        for field in ['title', 'department', 'location', 'job_type', 'experience_level',
                     'description', 'requirements', 'responsibilities', 'benefits',
                     'salary_min', 'salary_max', 'application_deadline', 'status']:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])
        
        # Set published_at when status changes to published
        if 'status' in data and data['status'] == 'published':
            fields.append('published_at = ?')
            values.append(datetime.now())
        
        fields.append('updated_at = ?')
        values.append(datetime.now())
        values.append(job_id)
        
        return Database.execute_query(
            f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?",
            tuple(values)
        )
    
    @staticmethod
    def delete(job_id: int) -> int:
        """Delete job posting"""
        return Database.execute_query(
            "DELETE FROM jobs WHERE id = ?",
            (job_id,)
        )
    
    @staticmethod
    def get_departments() -> List[str]:
        """Get distinct departments for filtering"""
        results = Database.execute_query(
            "SELECT DISTINCT department FROM jobs WHERE status = 'published' ORDER BY department",
            fetch='all'
        )
        return [row['department'] for row in results]
    
    @staticmethod
    def get_locations() -> List[str]:
        """Get distinct locations for filtering"""
        results = Database.execute_query(
            "SELECT DISTINCT location FROM jobs WHERE status = 'published' ORDER BY location",
            fetch='all'
        )
        return [row['location'] for row in results]