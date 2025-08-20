#!/usr/bin/env python3
"""
Matrica Networks - Database Initialization
Comprehensive SQLite schema with security-first approach
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'matrica.db')

def create_tables():
    """Create all database tables with proper constraints and indexes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Users table (employees and admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'employee')) DEFAULT 'employee',
            employee_id TEXT UNIQUE,
            department TEXT,
            designation TEXT,
            phone TEXT,
            date_joined DATE DEFAULT CURRENT_DATE,
            is_active BOOLEAN DEFAULT 1,
            last_login DATETIME,
            password_changed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table for secure authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            csrf_token TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # User sessions table for auth service
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            client_ip TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Note: Rate limiting tables are managed by auth.py
    
    # Security audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            client_ip TEXT,
            user_agent TEXT,
            details TEXT,
            success BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT CHECK(status IN ('planning', 'active', 'on_hold', 'completed', 'cancelled')) DEFAULT 'planning',
            priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
            start_date DATE,
            end_date DATE,
            deadline DATE,
            manager_id INTEGER,
            client_name TEXT,
            budget DECIMAL(10,2),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT CHECK(status IN ('todo', 'in_progress', 'review', 'completed', 'cancelled')) DEFAULT 'todo',
            priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
            assigned_to INTEGER,
            assigned_by INTEGER,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            start_date DATE,
            due_date DATE,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_by) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Tickets table for support/issue tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT CHECK(category IN ('bug', 'feature', 'support', 'security', 'maintenance')),
            priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
            status TEXT CHECK(status IN ('open', 'in_progress', 'resolved', 'closed', 'cancelled')) DEFAULT 'open',
            reporter_id INTEGER,
            assignee_id INTEGER,
            resolution TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            FOREIGN KEY (reporter_id) REFERENCES users (id) ON DELETE SET NULL,
            FOREIGN KEY (assignee_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            sign_in_time DATETIME,
            sign_out_time DATETIME,
            hours_worked DECIMAL(4,2),
            status TEXT CHECK(status IN ('present', 'absent', 'half_day', 'work_from_home')) DEFAULT 'present',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, date)
        )
    ''')
    
    # Leave requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            leave_type TEXT CHECK(leave_type IN ('annual', 'sick', 'personal', 'maternity', 'paternity', 'emergency')),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_requested INTEGER NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected', 'cancelled')) DEFAULT 'pending',
            approved_by INTEGER,
            approved_at DATETIME,
            rejection_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (approved_by) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            category TEXT CHECK(category IN ('handbook', 'policy', 'form', 'report', 'other')),
            uploaded_by INTEGER,
            is_public BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Contact inquiries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            organization TEXT,
            email TEXT NOT NULL,
            phone TEXT,
            reason TEXT NOT NULL,
            status TEXT CHECK(status IN ('new', 'in_progress', 'responded', 'closed')) DEFAULT 'new',
            assigned_to INTEGER,
            response TEXT,
            responded_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Blogs table (new feature)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT CHECK(type IN ('blog', 'post', 'case')) NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            author_id INTEGER NOT NULL,
            cover_image_path TEXT,
            status TEXT CHECK(status IN ('draft', 'published', 'archived')) DEFAULT 'draft',
            tags TEXT,
            views INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_at DATETIME,
            FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Audit log table for security tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Rate limiting table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            requests INTEGER DEFAULT 1,
            window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ip_address, endpoint)
        )
    ''')
    
    # Jobs table for careers management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            location TEXT NOT NULL,
            job_type TEXT CHECK(job_type IN ('full-time', 'part-time', 'contract', 'remote', 'hybrid')) DEFAULT 'full-time',
            experience_level TEXT CHECK(experience_level IN ('entry', 'mid', 'senior', 'lead', 'executive')) DEFAULT 'mid',
            description TEXT NOT NULL,
            requirements TEXT,
            responsibilities TEXT,
            benefits TEXT,
            salary_min INTEGER,
            salary_max INTEGER,
            application_deadline DATE,
            status TEXT CHECK(status IN ('draft', 'published', 'closed', 'filled')) DEFAULT 'draft',
            posted_by INTEGER,
            applications_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_at DATETIME,
            FOREIGN KEY (posted_by) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Create indexes for better performance
    cursor.executescript('''
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_security_audit_user ON security_audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_security_audit_time ON security_audit_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_security_audit_event ON security_audit_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
        CREATE INDEX IF NOT EXISTS idx_tickets_assignee_id ON tickets(assignee_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_user_id ON attendance(user_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_user_id ON leave_requests(user_id);
        CREATE INDEX IF NOT EXISTS idx_blogs_author_id ON blogs(author_id);
        CREATE INDEX IF NOT EXISTS idx_blogs_type ON blogs(type);
        CREATE INDEX IF NOT EXISTS idx_blogs_status ON blogs(status);
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_jobs_department ON jobs(department);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
        CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
        CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs(experience_level);
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database tables created successfully")

def hash_password(password, salt=None):
    """Hash password using PBKDF2 with salt"""
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Use PBKDF2 with 100,000 iterations
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    
    return password_hash, salt

def create_admin_user():
    """Create default admin user with specified credentials"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if admin user already exists
    cursor.execute("SELECT id FROM users WHERE username = 'psychy'")
    if cursor.fetchone():
        print("✓ Admin user already exists")
        conn.close()
        return
    
    # Create admin user
    password_hash, salt = hash_password("Ka05ml@2120")
    
    cursor.execute('''
        INSERT INTO users (
            username, email, password_hash, salt, first_name, last_name, 
            role, employee_id, department, designation, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'psychy',
        'admin@matricanetworks.com',
        password_hash,
        salt,
        'System',
        'Administrator',
        'admin',
        'EMP001',
        'IT',
        'System Administrator',
        1
    ))
    
    # Log the admin creation
    cursor.execute('''
        INSERT INTO audit_log (user_id, action, resource_type, details)
        VALUES (?, ?, ?, ?)
    ''', (
        cursor.lastrowid,
        'CREATE_ADMIN',
        'USER',
        'Initial admin user created during system setup'
    ))
    
    conn.commit()
    conn.close()
    print("✓ Admin user created successfully")
    print("  Username: psychy")
    print("  Password: Ka05ml@2120")

def insert_sample_data():
    """Insert sample data for demonstration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert sample employee
    password_hash, salt = hash_password("employee123")
    cursor.execute('''
        INSERT OR IGNORE INTO users (
            username, email, password_hash, salt, first_name, last_name, 
            role, employee_id, department, designation, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'john.doe',
        'john.doe@matricanetworks.com',
        password_hash,
        salt,
        'John',
        'Doe',
        'employee',
        'EMP002',
        'Cybersecurity',
        'Security Analyst',
        1
    ))
    
    # Insert sample project
    cursor.execute('''
        INSERT OR IGNORE INTO projects (
            name, description, status, priority, manager_id, client_name
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'Enterprise Security Assessment',
        'Comprehensive security assessment for Fortune 500 client',
        'active',
        'high',
        1,  # admin user
        'TechCorp Inc.'
    ))
    
    # Insert sample blog entries
    cursor.execute('''
        INSERT OR IGNORE INTO blogs (
            title, type, content, excerpt, author_id, status, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'The Future of Cybersecurity',
        'blog',
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit...',
        'Exploring emerging trends in cybersecurity...',
        1,  # admin user
        'published',
        datetime.now()
    ))
    
    cursor.execute('''
        INSERT OR IGNORE INTO blogs (
            title, type, content, excerpt, author_id, status, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Q4 Security Update',
        'post',
        'Our quarterly security update includes important information...',
        'Latest security updates and patches...',
        1,  # admin user
        'published',
        datetime.now()
    ))
    
    cursor.execute('''
        INSERT OR IGNORE INTO blogs (
            title, type, content, excerpt, author_id, status, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Banking Sector Penetration Test',
        'case',
        'Case study of our recent penetration testing engagement...',
        'How we helped a major bank improve their security posture...',
        1,  # admin user
        'published',
        datetime.now()
    ))
    
    # Insert sample job postings
    cursor.execute('''
        INSERT OR IGNORE INTO jobs (
            title, department, location, job_type, experience_level, description, 
            requirements, responsibilities, benefits, salary_min, salary_max, 
            status, posted_by, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Senior Cybersecurity Analyst',
        'Cybersecurity',
        'San Francisco, CA / Remote',
        'full-time',
        'senior',
        'Join our elite cybersecurity team to protect enterprise clients from advanced persistent threats.',
        'Bachelor\'s degree in Computer Science or Cybersecurity, CISSP certification preferred, 5+ years experience in SOC operations, expertise in SIEM tools',
        'Monitor security events, conduct threat hunting, perform incident response, develop security policies, mentor junior analysts',
        'Competitive salary, health insurance, retirement plan, professional development budget, flexible work arrangements',
        120000,
        150000,
        'published',
        1,
        datetime.now()
    ))
    
    cursor.execute('''
        INSERT OR IGNORE INTO jobs (
            title, department, location, job_type, experience_level, description, 
            requirements, responsibilities, benefits, salary_min, salary_max, 
            status, posted_by, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Penetration Tester',
        'Cybersecurity',
        'New York, NY / Remote',
        'full-time',
        'mid',
        'Conduct comprehensive penetration testing engagements for Fortune 500 clients.',
        'OSCP, CEH, or equivalent certification, 3+ years penetration testing experience, knowledge of web application security',
        'Perform network and application penetration tests, write detailed reports, present findings to clients, develop custom exploits',
        'Competitive salary, health insurance, retirement plan, conference attendance, certification reimbursement',
        95000,
        120000,
        'published',
        1,
        datetime.now()
    ))
    
    cursor.execute('''
        INSERT OR IGNORE INTO jobs (
            title, department, location, job_type, experience_level, description, 
            requirements, responsibilities, benefits, salary_min, salary_max, 
            status, posted_by, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Junior Security Engineer',
        'Engineering',
        'Austin, TX / Hybrid',
        'full-time',
        'entry',
        'Entry-level position for passionate cybersecurity graduates to start their career.',
        'Bachelor\'s degree in Computer Science, Cybersecurity, or related field, Security+ certification preferred, internship experience in security',
        'Assist with security assessments, maintain security tools, document procedures, participate in incident response',
        'Competitive salary, comprehensive training program, mentorship, health insurance, career development opportunities',
        65000,
        80000,
        'published',
        1,
        datetime.now()
    ))
    
    conn.commit()
    conn.close()
    print("✓ Sample data inserted successfully")

def main():
    """Initialize the complete database"""
    print("Initializing Matrica Networks Database...")
    print(f"Database location: {DB_PATH}")
    
    # Create tables
    create_tables()
    
    # Create admin user
    create_admin_user()
    
    # Insert sample data
    insert_sample_data()
    
    print("\n🎉 Database initialization completed successfully!")
    print("\nYou can now start the server with: python backend/server.py")

if __name__ == "__main__":
    main()