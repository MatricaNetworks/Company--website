#!/usr/bin/env python3
"""
Matrica Networks - Core Web Server
Pure Python HTTP server with security-first approach
Using only standard library (wsgiref.simple_server)
"""

import os
import sys
import json
import mimetypes
from wsgiref.simple_server import make_server, WSGIServer
from urllib.parse import parse_qs, urlparse
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from models import Database, User, Session, Project, Task, Blog, Contact, AuditLog, RateLimit
from middleware import SecurityMiddleware, AuthMiddleware
from controllers import AuthController, EmployeeController, ProjectController, BlogController, ContactController, JobController
from auth import init_auth_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MatricaWSGIApp:
    """Main WSGI application with routing and middleware"""
    
    def __init__(self):
        self.frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
        self.storage_path = os.path.join(os.path.dirname(__file__), 'storage')
        
        # Initialize controllers
        self.auth_controller = AuthController()
        self.employee_controller = EmployeeController()
        self.project_controller = ProjectController()
        self.blog_controller = BlogController()
        self.contact_controller = ContactController()
        self.job_controller = JobController()
        
        # Initialize middleware
        self.security_middleware = SecurityMiddleware()
        self.auth_middleware = AuthMiddleware()
        
        # Define API routes
        self.api_routes = {
            # Authentication routes
            'POST /api/auth/login': self.auth_controller.login,
            'POST /api/auth/logout': self.auth_controller.logout,
            'GET /api/me': self.auth_controller.me,
            
            # Employee routes (admin only)
            'GET /api/employees': self.employee_controller.list,
            'POST /api/employees': self.employee_controller.create,
            'GET /api/employees/{id}': self.employee_controller.get,
            'PUT /api/employees/{id}': self.employee_controller.update,
            'DELETE /api/employees/{id}': self.employee_controller.delete,
            
            # Project routes
            'GET /api/projects': self.project_controller.list,
            'POST /api/projects': self.project_controller.create,
            'GET /api/projects/{id}': self.project_controller.get,
            'PUT /api/projects/{id}': self.project_controller.update,
            'DELETE /api/projects/{id}': self.project_controller.delete,
            
            # Task routes
            'GET /api/tasks': self.project_controller.list_tasks,
            'POST /api/tasks': self.project_controller.create_task,
            'PUT /api/tasks/{id}': self.project_controller.update_task,
            
            # Blog routes
            'GET /api/blogs': self.blog_controller.list,
            'POST /api/blogs': self.blog_controller.create,
            'GET /api/blogs/{id}': self.blog_controller.get,
            'PUT /api/blogs/{id}': self.blog_controller.update,
            'DELETE /api/blogs/{id}': self.blog_controller.delete,
            
            # Contact route
            'POST /api/contact': self.contact_controller.submit,
            
            # Public job routes
            'GET /api/jobs': self.job_controller.get_public_jobs,
            'GET /api/jobs/{id}': self.job_controller.get_job_detail,
            
            # Admin job routes
            'GET /api/admin/jobs': self.job_controller.get_all_jobs,
            'POST /api/admin/jobs': self.job_controller.create_job,
            'PUT /api/admin/jobs/{id}': self.job_controller.update_job,
            'DELETE /api/admin/jobs/{id}': self.job_controller.delete_job,
            
            # Admin routes
            'GET /api/admin/audit-log': self.get_audit_log,
            'GET /api/admin/dashboard': self.get_dashboard_stats,
        }
        
        logger.info("Matrica WSGI Application initialized")
    
    def __call__(self, environ, start_response):
        """WSGI application entry point"""
        try:
            # Get request information
            method = environ['REQUEST_METHOD']
            path = environ['PATH_INFO']
            query_string = environ.get('QUERY_STRING', '')
            
            # Get client info for security
            client_ip = environ.get('REMOTE_ADDR', 'unknown')
            user_agent = environ.get('HTTP_USER_AGENT', 'unknown')
            
            # Log request
            logger.info(f"{method} {path} - {client_ip}")
            
            # Apply security middleware
            security_result = self.security_middleware.process_request(environ)
            if security_result:
                return self._error_response(start_response, *security_result)
            
            # Rate limiting (handled by auth service for auth endpoints)
            # if not RateLimit.check_rate_limit(client_ip, path):
            #     logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            #     return self._error_response(start_response, 429, {'error': 'Rate limit exceeded'})
            
            # Handle API routes
            if path.startswith('/api/'):
                return self._handle_api(environ, start_response, method, path, client_ip, user_agent)
            
            # Handle static files
            return self._serve_static(environ, start_response, path)
            
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            return self._error_response(start_response, 500, {'error': 'Internal server error'})
    
    def _handle_api(self, environ, start_response, method: str, path: str, 
                   client_ip: str, user_agent: str):
        """Handle API requests"""
        try:
            # Parse request body for POST/PUT requests
            request_body = {}
            if method in ['POST', 'PUT']:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    body = environ['wsgi.input'].read(content_length).decode('utf-8')
                    try:
                        request_body = json.loads(body)
                    except json.JSONDecodeError:
                        return self._error_response(start_response, 400, {'error': 'Invalid JSON'})
            
            # Parse query parameters
            query_params = parse_qs(environ.get('QUERY_STRING', ''))
            
            # Find matching route
            route_key, params = self._match_route(method, path)
            if not route_key:
                return self._error_response(start_response, 404, {'error': 'Endpoint not found'})
            
            handler = self.api_routes[route_key]
            
            # Check authentication for protected routes
            session = None
            if not path.startswith('/api/auth/login') and not path.startswith('/api/contact'):
                auth_result = self.auth_middleware.process_request(environ)
                if isinstance(auth_result, tuple):  # Error response
                    return self._error_response(start_response, *auth_result)
                session = auth_result
            
            # Prepare request context
            request_context = {
                'method': method,
                'path': path,
                'body': request_body,
                'query': query_params,
                'params': params,
                'session': session,
                'client_ip': client_ip,
                'user_agent': user_agent
            }
            
            # Call handler
            response = handler(request_context)
            
            # Return JSON response
            return self._json_response(start_response, 200, response)
            
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return self._error_response(start_response, 500, {'error': 'Internal server error'})
    
    def _match_route(self, method: str, path: str) -> Tuple[Optional[str], Dict]:
        """Match request to route pattern and extract parameters"""
        for route_pattern, handler in self.api_routes.items():
            route_method, route_path = route_pattern.split(' ', 1)
            
            if route_method != method:
                continue
            
            # Handle parameterized routes
            if '{' in route_path:
                # Simple parameter matching
                pattern_parts = route_path.split('/')
                path_parts = path.split('/')
                
                if len(pattern_parts) != len(path_parts):
                    continue
                
                params = {}
                match = True
                
                for i, (pattern_part, path_part) in enumerate(zip(pattern_parts, path_parts)):
                    if pattern_part.startswith('{') and pattern_part.endswith('}'):
                        param_name = pattern_part[1:-1]
                        params[param_name] = path_part
                    elif pattern_part != path_part:
                        match = False
                        break
                
                if match:
                    return route_pattern, params
            else:
                # Exact match
                if route_path == path:
                    return route_pattern, {}
        
        return None, {}
    
    def _serve_static(self, environ, start_response, path: str):
        """Serve static files"""
        # Default to index.html for root
        if path == '/' or path == '':
            path = '/index.html'
        
        # Security: prevent directory traversal
        if '..' in path or path.startswith('../'):
            return self._error_response(start_response, 403, {'error': 'Forbidden'})
        
        # Map paths to filesystem
        file_path = os.path.join(self.frontend_path, path.lstrip('/'))
        
        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            # Try with .html extension
            html_path = file_path + '.html'
            if os.path.exists(html_path) and os.path.isfile(html_path):
                file_path = html_path
            else:
                return self._error_response(start_response, 404, {'error': 'File not found'})
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Read and serve file
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Security headers
            headers = [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content))),
                ('X-Content-Type-Options', 'nosniff'),
                ('X-Frame-Options', 'DENY'),
                ('X-XSS-Protection', '1; mode=block')
            ]
            
            start_response('200 OK', headers)
            return [content]
            
        except Exception as e:
            logger.error(f"Error serving static file {file_path}: {str(e)}")
            return self._error_response(start_response, 500, {'error': 'Server error'})
    
    def _json_response(self, start_response, status_code: int, data: Dict):
        """Return JSON response"""
        response_body = json.dumps(data, default=str).encode('utf-8')
        
        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(response_body))),
            ('X-Content-Type-Options', 'nosniff'),
            ('X-Frame-Options', 'DENY'),
            ('X-XSS-Protection', '1; mode=block')
        ]
        
        status_text = f"{status_code} OK" if status_code == 200 else f"{status_code} Error"
        start_response(status_text, headers)
        return [response_body]
    
    def _error_response(self, start_response, status_code: int, data: Dict):
        """Return error response"""
        return self._json_response(start_response, status_code, data)
    
    def get_audit_log(self, request_context: Dict) -> Dict:
        """Get audit log (admin only)"""
        if not request_context['session'] or request_context['session']['user']['role'] != 'admin':
            raise Exception("Unauthorized")
        
        logs = AuditLog.get_recent(50)
        return {'logs': logs}
    
    def get_dashboard_stats(self, request_context: Dict) -> Dict:
        """Get dashboard statistics (admin only)"""
        if not request_context['session'] or request_context['session']['user']['role'] != 'admin':
            raise Exception("Unauthorized")
        
        # Get various statistics
        users = Database.execute_query("SELECT COUNT(*) as count FROM users WHERE is_active = 1", fetch='one')
        projects = Database.execute_query("SELECT COUNT(*) as count FROM projects", fetch='one')
        tasks = Database.execute_query("SELECT COUNT(*) as count FROM tasks", fetch='one')
        blogs = Database.execute_query("SELECT COUNT(*) as count FROM blogs WHERE status = 'published'", fetch='one')
        
        return {
            'stats': {
                'users': users['count'],
                'projects': projects['count'],
                'tasks': tasks['count'],
                'blogs': blogs['count']
            }
        }

class ThreadingWSGIServer(WSGIServer):
    """Multi-threaded WSGI server"""
    def server_bind(self):
        super().server_bind()
        self.server_name = "Matrica-Server"
        self.server_port = self.server_address[1]

def main():
    """Start the Matrica Networks server"""
    # Initialize database
    print("Initializing database...")
    db_path = os.path.join(os.path.dirname(__file__), 'matrica.db')
    os.system(f"cd {os.path.dirname(__file__)} && python db_init.py")
    
    # Initialize authentication service
    print("Initializing authentication service...")
    init_auth_service(db_path)
    
    # Create WSGI application
    app = MatricaWSGIApp()
    
    # Create server
    server = make_server('localhost', 8003, app, server_class=ThreadingWSGIServer)
    
    print("\n" + "="*50)
    print("🛡️  MATRICA NETWORKS - CYBERSECURITY PLATFORM")
    print("="*50)
    print(f"🚀 Server running on: http://localhost:8003")
    print(f"📁 Frontend path: {app.frontend_path}")
    print(f"💾 Database: {os.path.join(os.path.dirname(__file__), 'matrica.db')}")
    print("\n🔐 Admin Credentials:")
    print("   Username: psychy")
    print("   Password: Ka05ml@2120")
    print("\n📚 Available endpoints:")
    print("   • http://localhost:8003/ - Main website")
    print("   • http://localhost:8003/portal/login.html - Employee portal")
    print("   • http://localhost:8003/api/ - REST API endpoints")
    print("\n⚡ Press Ctrl+C to stop the server")
    print("="*50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⭐ Matrica Networks server stopped. Stay secure!")

if __name__ == "__main__":
    main()