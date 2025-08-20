#!/usr/bin/env python3
"""
Matrica Networks - API Controllers
Comprehensive controllers for all API endpoints
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from models import Database, User, Session, Project, Task, Blog, Contact, AuditLog, Job
from middleware import InputValidationMiddleware
from auth import get_auth_service

logger = logging.getLogger(__name__)

class BaseController:
    """Base controller with common functionality"""
    
    def __init__(self):
        self.validator = InputValidationMiddleware()
    
    def validate_admin_access(self, session: Dict) -> bool:
        """Check if user has admin access"""
        return session and session['user']['role'] == 'admin'
    
    def log_action(self, user_id: int, action: str, resource_type: str = None, 
                  resource_id: str = None, details: str = None, 
                  ip_address: str = None, user_agent: str = None):
        """Log user action"""
        AuditLog.log(user_id, action, resource_type, resource_id, details, ip_address, user_agent)

class AuthController(BaseController):
    """Authentication controller"""
    
    def login(self, request_context: Dict) -> Dict:
        """Handle user login"""
        try:
            data = request_context['body']
            client_ip = request_context['client_ip']
            user_agent = request_context['user_agent']
            
            # Validate input
            is_valid, errors = self.validator.validate_input(data, {
                'username': 'username_required',
                'password': 'password_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Get auth service
            auth_service = get_auth_service()
            if not auth_service:
                return {'success': False, 'error': 'Authentication service unavailable'}
            
            # Authenticate user
            user = auth_service.authenticate_user(
                data['username'], 
                data['password'], 
                client_ip, 
                user_agent
            )
            
            if not user:
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Create session
            session_token = auth_service.create_session(
                user['id'], 
                client_ip, 
                user_agent, 
                data.get('remember', False)
            )
            
            if not session_token:
                return {'success': False, 'error': 'Failed to create session'}
            
            return {
                'success': True,
                'user': user,
                'session_token': session_token
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {'success': False, 'error': 'Login failed'}
    
    def logout(self, request_context: Dict) -> Dict:
        """Handle user logout"""
        try:
            session_token = request_context.get('session_token')
            if session_token:
                auth_service = get_auth_service()
                if auth_service:
                    auth_service.logout_session(session_token)
            
            return {'success': True, 'message': 'Logged out successfully'}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': 'Logout failed'}
    
    def me(self, request_context: Dict) -> Dict:
        """Get current user information"""
        try:
            session_token = request_context.get('session_token')
            if not session_token:
                return {'success': False, 'authenticated': False, 'error': 'Not authenticated'}
            
            auth_service = get_auth_service()
            if not auth_service:
                return {'success': False, 'authenticated': False, 'error': 'Authentication service unavailable'}
            
            user = auth_service.validate_session(session_token)
            if not user:
                return {'success': False, 'authenticated': False, 'error': 'Invalid session'}
            
            return {
                'success': True,
                'authenticated': True,
                'user': user
            }
            
        except Exception as e:
            logger.error(f"Me endpoint error: {str(e)}")
            return {'success': False, 'authenticated': False, 'error': 'Failed to get user info'}

class EmployeeController(BaseController):
    """Employee management controller (admin only)"""
    
    def list(self, request_context: Dict) -> Dict:
        """List all employees"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            users = User.get_all()
            # Remove sensitive data
            users_safe = []
            for user in users:
                user_safe = {k: v for k, v in user.items() if k not in ['password_hash', 'salt']}
                users_safe.append(user_safe)
            
            return {'success': True, 'employees': users_safe}
            
        except Exception as e:
            logger.error(f"List employees error: {str(e)}")
            return {'success': False, 'error': 'Failed to list employees'}
    
    def create(self, request_context: Dict) -> Dict:
        """Create new employee"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            data = request_context['body']
            
            # Validate input
            is_valid, errors = self.validator.validate_input(data, {
                'username': 'username_required',
                'email': 'email_required',
                'password': 'password_required',
                'first_name': 'name_required',
                'last_name': 'name_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Create user
            user_id = User.create(data)
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='CREATE_EMPLOYEE',
                resource_type='USER',
                resource_id=str(user_id),
                details=f"Created employee: {data['username']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'employee_id': user_id}
            
        except Exception as e:
            logger.error(f"Create employee error: {str(e)}")
            return {'success': False, 'error': 'Failed to create employee'}
    
    def get(self, request_context: Dict) -> Dict:
        """Get employee by ID"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            user_id = int(request_context['params']['id'])
            user = User.get_by_id(user_id)
            
            if not user:
                return {'success': False, 'error': 'Employee not found'}
            
            # Remove sensitive data
            user_safe = {k: v for k, v in user.items() if k not in ['password_hash', 'salt']}
            
            return {'success': True, 'employee': user_safe}
            
        except Exception as e:
            logger.error(f"Get employee error: {str(e)}")
            return {'success': False, 'error': 'Failed to get employee'}
    
    def update(self, request_context: Dict) -> Dict:
        """Update employee"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            user_id = int(request_context['params']['id'])
            data = request_context['body']
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Update user
            rows_affected = User.update(user_id, data)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Employee not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='UPDATE_EMPLOYEE',
                resource_type='USER',
                resource_id=str(user_id),
                details=f"Updated employee ID: {user_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Employee updated successfully'}
            
        except Exception as e:
            logger.error(f"Update employee error: {str(e)}")
            return {'success': False, 'error': 'Failed to update employee'}
    
    def delete(self, request_context: Dict) -> Dict:
        """Delete (deactivate) employee"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            user_id = int(request_context['params']['id'])
            
            # Soft delete user
            rows_affected = User.delete(user_id)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Employee not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='DELETE_EMPLOYEE',
                resource_type='USER',
                resource_id=str(user_id),
                details=f"Deactivated employee ID: {user_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Employee deactivated successfully'}
            
        except Exception as e:
            logger.error(f"Delete employee error: {str(e)}")
            return {'success': False, 'error': 'Failed to delete employee'}

class ProjectController(BaseController):
    """Project and task management controller"""
    
    def list(self, request_context: Dict) -> Dict:
        """List all projects"""
        try:
            projects = Project.get_all()
            return {'success': True, 'projects': projects}
            
        except Exception as e:
            logger.error(f"List projects error: {str(e)}")
            return {'success': False, 'error': 'Failed to list projects'}
    
    def create(self, request_context: Dict) -> Dict:
        """Create new project (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            data = request_context['body']
            
            # Validate input
            is_valid, errors = self.validator.validate_input(data, {
                'name': 'safe_text_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Create project
            project_id = Project.create(data)
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='CREATE_PROJECT',
                resource_type='PROJECT',
                resource_id=str(project_id),
                details=f"Created project: {data['name']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'project_id': project_id}
            
        except Exception as e:
            logger.error(f"Create project error: {str(e)}")
            return {'success': False, 'error': 'Failed to create project'}
    
    def get(self, request_context: Dict) -> Dict:
        """Get project by ID"""
        try:
            project_id = int(request_context['params']['id'])
            project = Project.get_by_id(project_id)
            
            if not project:
                return {'success': False, 'error': 'Project not found'}
            
            return {'success': True, 'project': project}
            
        except Exception as e:
            logger.error(f"Get project error: {str(e)}")
            return {'success': False, 'error': 'Failed to get project'}
    
    def update(self, request_context: Dict) -> Dict:
        """Update project (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            project_id = int(request_context['params']['id'])
            data = request_context['body']
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Update project
            rows_affected = Project.update(project_id, data)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Project not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='UPDATE_PROJECT',
                resource_type='PROJECT',
                resource_id=str(project_id),
                details=f"Updated project ID: {project_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Project updated successfully'}
            
        except Exception as e:
            logger.error(f"Update project error: {str(e)}")
            return {'success': False, 'error': 'Failed to update project'}
    
    def delete(self, request_context: Dict) -> Dict:
        """Delete project (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            project_id = int(request_context['params']['id'])
            
            # Delete project
            rows_affected = Project.delete(project_id)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Project not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='DELETE_PROJECT',
                resource_type='PROJECT',
                resource_id=str(project_id),
                details=f"Deleted project ID: {project_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Project deleted successfully'}
            
        except Exception as e:
            logger.error(f"Delete project error: {str(e)}")
            return {'success': False, 'error': 'Failed to delete project'}
    
    def list_tasks(self, request_context: Dict) -> Dict:
        """List tasks (user sees assigned tasks, admin sees all)"""
        try:
            session = request_context['session']
            
            if session['user']['role'] == 'admin':
                tasks = Task.get_all()
            else:
                tasks = Task.get_by_user(session['user']['id'])
            
            return {'success': True, 'tasks': tasks}
            
        except Exception as e:
            logger.error(f"List tasks error: {str(e)}")
            return {'success': False, 'error': 'Failed to list tasks'}
    
    def create_task(self, request_context: Dict) -> Dict:
        """Create new task (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            data = request_context['body']
            
            # Validate input
            is_valid, errors = self.validator.validate_input(data, {
                'title': 'safe_text_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            data['assigned_by'] = request_context['session']['user']['id']
            
            # Create task
            task_id = Task.create(data)
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='CREATE_TASK',
                resource_type='TASK',
                resource_id=str(task_id),
                details=f"Created task: {data['title']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'task_id': task_id}
            
        except Exception as e:
            logger.error(f"Create task error: {str(e)}")
            return {'success': False, 'error': 'Failed to create task'}
    
    def update_task(self, request_context: Dict) -> Dict:
        """Update task"""
        try:
            task_id = int(request_context['params']['id'])
            data = request_context['body']
            session = request_context['session']
            
            # For employees, only allow status updates on assigned tasks
            if session['user']['role'] != 'admin':
                # Check if task is assigned to this user
                task = Database.execute_query(
                    "SELECT assigned_to FROM tasks WHERE id = ?", 
                    (task_id,), 
                    'one'
                )
                
                if not task or task['assigned_to'] != session['user']['id']:
                    return {'success': False, 'error': 'Task not found or not assigned to you'}
                
                # Only allow status updates
                allowed_fields = ['status', 'actual_hours']
                data = {k: v for k, v in data.items() if k in allowed_fields}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Update task
            rows_affected = Database.execute_query(
                "UPDATE tasks SET status = COALESCE(?, status), actual_hours = COALESCE(?, actual_hours), updated_at = ? WHERE id = ?",
                (data.get('status'), data.get('actual_hours'), datetime.now(), task_id)
            )
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Task not found'}
            
            # Log action
            self.log_action(
                user_id=session['user']['id'],
                action='UPDATE_TASK',
                resource_type='TASK',
                resource_id=str(task_id),
                details=f"Updated task ID: {task_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Task updated successfully'}
            
        except Exception as e:
            logger.error(f"Update task error: {str(e)}")
            return {'success': False, 'error': 'Failed to update task'}

class BlogController(BaseController):
    """Blog management controller"""
    
    def list(self, request_context: Dict) -> Dict:
        """List published blogs (public) or all blogs (admin)"""
        try:
            query_params = request_context['query']
            blog_type = query_params.get('type', [None])[0]
            
            session = request_context.get('session')
            
            if session and session['user']['role'] == 'admin':
                # Admin sees all blogs
                if blog_type:
                    blogs = Database.execute_query('''
                        SELECT b.*, u.first_name || ' ' || u.last_name as author_name
                        FROM blogs b
                        JOIN users u ON b.author_id = u.id
                        WHERE b.type = ?
                        ORDER BY b.created_at DESC
                    ''', (blog_type,), 'all')
                else:
                    blogs = Database.execute_query('''
                        SELECT b.*, u.first_name || ' ' || u.last_name as author_name
                        FROM blogs b
                        JOIN users u ON b.author_id = u.id
                        ORDER BY b.created_at DESC
                    ''', fetch='all')
            else:
                # Public sees only published blogs
                blogs = Blog.get_published(blog_type)
            
            return {'success': True, 'blogs': blogs}
            
        except Exception as e:
            logger.error(f"List blogs error: {str(e)}")
            return {'success': False, 'error': 'Failed to list blogs'}
    
    def get(self, request_context: Dict) -> Dict:
        """Get blog by ID"""
        try:
            blog_id = int(request_context['params']['id'])
            blog = Blog.get_by_id(blog_id)
            
            if not blog:
                return {'success': False, 'error': 'Blog not found'}
            
            # Public can only see published blogs
            session = request_context.get('session')
            if not session or session['user']['role'] != 'admin':
                if blog['status'] != 'published':
                    return {'success': False, 'error': 'Blog not found'}
            
            # Increment view count
            Database.execute_query(
                "UPDATE blogs SET views = views + 1 WHERE id = ?",
                (blog_id,)
            )
            
            return {'success': True, 'blog': blog}
            
        except Exception as e:
            logger.error(f"Get blog error: {str(e)}")
            return {'success': False, 'error': 'Failed to get blog'}
    
    def create(self, request_context: Dict) -> Dict:
        """Create new blog (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            data = request_context['body']
            
            # Validate input
            is_valid, errors = self.validator.validate_input(data, {
                'title': 'safe_text_required',
                'content': 'safe_text_required',
                'type': 'safe_text_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            data['author_id'] = request_context['session']['user']['id']
            
            # Create blog
            blog_id = Blog.create(data)
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='CREATE_BLOG',
                resource_type='BLOG',
                resource_id=str(blog_id),
                details=f"Created blog: {data['title']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'blog_id': blog_id}
            
        except Exception as e:
            logger.error(f"Create blog error: {str(e)}")
            return {'success': False, 'error': 'Failed to create blog'}
    
    def update(self, request_context: Dict) -> Dict:
        """Update blog (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            blog_id = int(request_context['params']['id'])
            data = request_context['body']
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Update blog
            rows_affected = Blog.update(blog_id, data)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Blog not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='UPDATE_BLOG',
                resource_type='BLOG',
                resource_id=str(blog_id),
                details=f"Updated blog ID: {blog_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Blog updated successfully'}
            
        except Exception as e:
            logger.error(f"Update blog error: {str(e)}")
            return {'success': False, 'error': 'Failed to update blog'}
    
    def delete(self, request_context: Dict) -> Dict:
        """Delete blog (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            blog_id = int(request_context['params']['id'])
            
            # Delete blog
            rows_affected = Blog.delete(blog_id)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Blog not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='DELETE_BLOG',
                resource_type='BLOG',
                resource_id=str(blog_id),
                details=f"Deleted blog ID: {blog_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Blog deleted successfully'}
            
        except Exception as e:
            logger.error(f"Delete blog error: {str(e)}")
            return {'success': False, 'error': 'Failed to delete blog'}

class ContactController(BaseController):
    """Contact form controller"""
    
    def submit(self, request_context: Dict) -> Dict:
        """Submit contact form (public endpoint)"""
        try:
            data = request_context['body']
            
            # Validate input
            is_valid, errors = self.validator.validate_input(data, {
                'name': 'name_required',
                'email': 'email_required',
                'reason': 'safe_text_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Create contact inquiry
            inquiry_id = Contact.create(data)
            
            # Log submission
            logger.info(f"Contact form submitted: {data['email']} - {data['name']}")
            
            # Log action (no user ID for public endpoint)
            AuditLog.log(
                user_id=None,
                action='CONTACT_SUBMISSION',
                resource_type='CONTACT',
                resource_id=str(inquiry_id),
                details=f"Contact form submission from {data['email']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {
                'success': True, 
                'message': 'Thank you for your inquiry. We will get back to you soon.',
                'inquiry_id': inquiry_id
            }
            
        except Exception as e:
            logger.error(f"Contact submission error: {str(e)}")
            return {'success': False, 'error': 'Failed to submit contact form'}

class JobController(BaseController):
    """Job posting controller"""
    
    def get_public_jobs(self, request_context: Dict) -> Dict:
        """Get published jobs for public careers page"""
        try:
            # Get query parameters for filtering
            params = request_context.get('query_params', {})
            department = params.get('department')
            location = params.get('location')
            job_type = params.get('job_type')
            experience_level = params.get('experience_level')
            
            if any([department, location, job_type, experience_level]):
                jobs = Job.get_by_filters(department, location, job_type, experience_level)
            else:
                jobs = Job.get_published()
            
            # Get filter options
            departments = Job.get_departments()
            locations = Job.get_locations()
            
            return {
                'success': True,
                'jobs': jobs,
                'filters': {
                    'departments': departments,
                    'locations': locations,
                    'job_types': ['full-time', 'part-time', 'contract', 'remote', 'hybrid'],
                    'experience_levels': ['entry', 'mid', 'senior', 'lead', 'executive']
                }
            }
            
        except Exception as e:
            logger.error(f"Get public jobs error: {str(e)}")
            return {'success': False, 'error': 'Failed to load jobs'}
    
    def get_job_detail(self, request_context: Dict) -> Dict:
        """Get single job detail for public viewing"""
        try:
            job_id = int(request_context['params']['id'])
            job = Job.get_by_id(job_id)
            
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            # Only show published jobs to public
            if job['status'] != 'published':
                return {'success': False, 'error': 'Job not available'}
            
            return {'success': True, 'job': job}
            
        except Exception as e:
            logger.error(f"Get job detail error: {str(e)}")
            return {'success': False, 'error': 'Failed to load job'}
    
    def get_all_jobs(self, request_context: Dict) -> Dict:
        """Get all jobs for admin management"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            jobs = Job.get_all()
            return {'success': True, 'jobs': jobs}
            
        except Exception as e:
            logger.error(f"Get all jobs error: {str(e)}")
            return {'success': False, 'error': 'Failed to load jobs'}
    
    def create_job(self, request_context: Dict) -> Dict:
        """Create new job posting (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            data = request_context['body']
            
            # Validate required fields
            is_valid, errors = self.validator.validate_input(data, {
                'title': 'safe_text_required',
                'department': 'safe_text_required',
                'location': 'safe_text_required',
                'description': 'safe_text_required'
            })
            
            if not is_valid:
                return {'success': False, 'errors': errors}
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Set poster
            data['posted_by'] = request_context['session']['user']['id']
            
            # Create job
            job_id = Job.create(data)
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='CREATE_JOB',
                resource_type='JOB',
                resource_id=str(job_id),
                details=f"Created job: {data['title']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Job created successfully', 'job_id': job_id}
            
        except Exception as e:
            logger.error(f"Create job error: {str(e)}")
            return {'success': False, 'error': 'Failed to create job'}
    
    def update_job(self, request_context: Dict) -> Dict:
        """Update job posting (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            job_id = int(request_context['params']['id'])
            data = request_context['body']
            
            # Sanitize input
            data = self.validator.sanitize_input(data)
            
            # Update job
            rows_affected = Job.update(job_id, data)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Job not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='UPDATE_JOB',
                resource_type='JOB',
                resource_id=str(job_id),
                details=f"Updated job ID: {job_id}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Job updated successfully'}
            
        except Exception as e:
            logger.error(f"Update job error: {str(e)}")
            return {'success': False, 'error': 'Failed to update job'}
    
    def delete_job(self, request_context: Dict) -> Dict:
        """Delete job posting (admin only)"""
        try:
            if not self.validate_admin_access(request_context['session']):
                return {'success': False, 'error': 'Admin access required'}
            
            job_id = int(request_context['params']['id'])
            
            # Get job info for logging
            job = Job.get_by_id(job_id)
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            # Delete job
            rows_affected = Job.delete(job_id)
            
            if rows_affected == 0:
                return {'success': False, 'error': 'Job not found'}
            
            # Log action
            self.log_action(
                user_id=request_context['session']['user']['id'],
                action='DELETE_JOB',
                resource_type='JOB',
                resource_id=str(job_id),
                details=f"Deleted job: {job['title']}",
                ip_address=request_context['client_ip'],
                user_agent=request_context['user_agent']
            )
            
            return {'success': True, 'message': 'Job deleted successfully'}
            
        except Exception as e:
            logger.error(f"Delete job error: {str(e)}")
            return {'success': False, 'error': 'Failed to delete job'}