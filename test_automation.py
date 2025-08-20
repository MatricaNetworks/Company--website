#!/usr/bin/env python3
"""
Matrica Networks - Automation Testing Script
Comprehensive testing for authentication, security, and UI functionality
"""

import os
import sys
import json
import time
import requests
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MatricaTestSuite:
    """Comprehensive test suite for Matrica Networks website"""
    
    def __init__(self, base_url: str, output_file: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.output_file = output_file
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 10
        
        # Test user credentials for authentication testing
        self.test_users = {
            'admin': {
                'username': 'psychy',
                'password': 'Ka05ml@2120',
                'role': 'admin'
            },
            'employee': {
                'username': 'john.doe',
                'password': 'employee123',
                'role': 'employee'
            }
        }
    
    def log_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results.append(result)
        
        status_emoji = {'PASS': '✓', 'FAIL': '✗', 'WARN': '⚠', 'INFO': 'ℹ'}
        print(f"{status_emoji.get(status, '?')} {test_name}: {message}")
        
        if status == 'FAIL':
            logger.error(f"{test_name}: {message}")
    
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                self.log_result("Server Connectivity", "PASS", "Server is accessible")
            else:
                self.log_result("Server Connectivity", "FAIL", 
                              f"Server returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.log_result("Server Connectivity", "FAIL", f"Cannot connect to server: {str(e)}")
    
    def test_login_page_accessibility(self):
        """Test login page loads correctly"""
        try:
            url = urljoin(self.base_url, '/portal/login.html')
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.log_result("Login Page Access", "FAIL", 
                              f"Login page returned status {response.status_code}")
                return
            
            content = response.text
            
            # Check for essential login elements
            checks = {
                'login_form': r'<form[^>]*id=["\']login-form["\']',
                'username_field': r'<input[^>]*name=["\']username["\']',
                'password_field': r'<input[^>]*name=["\']password["\']',
                'login_button': r'<button[^>]*type=["\']submit["\']',
                'matrix_canvas': r'<canvas[^>]*id=["\']matrix-rain["\']',
            }
            
            missing_elements = []
            for element, pattern in checks.items():
                if not re.search(pattern, content, re.IGNORECASE):
                    missing_elements.append(element)
            
            if missing_elements:
                self.log_result("Login Page Elements", "FAIL", 
                              f"Missing elements: {', '.join(missing_elements)}")
            else:
                self.log_result("Login Page Elements", "PASS", "All login elements present")
                
        except requests.exceptions.RequestException as e:
            self.log_result("Login Page Access", "FAIL", f"Error accessing login page: {str(e)}")
    
    def test_css_files_loading(self):
        """Test that CSS files load correctly"""
        css_files = [
            '/assets/css/base.css',
            '/assets/css/layout.css', 
            '/assets/css/components.css',
            '/assets/css/neon.css'
        ]
        
        for css_file in css_files:
            try:
                url = urljoin(self.base_url, css_file)
                response = self.session.get(url)
                
                if response.status_code == 200:
                    # Check if it's actually CSS content
                    content_type = response.headers.get('content-type', '')
                    if 'text/css' in content_type or css_file.endswith('.css'):
                        self.log_result(f"CSS File {css_file}", "PASS", "CSS file loads correctly")
                    else:
                        self.log_result(f"CSS File {css_file}", "WARN", 
                                      f"Unexpected content type: {content_type}")
                else:
                    self.log_result(f"CSS File {css_file}", "FAIL", 
                                  f"CSS file returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_result(f"CSS File {css_file}", "FAIL", 
                              f"Error loading CSS file: {str(e)}")
    
    def test_login_styling(self):
        """Test login page styling and centering"""
        try:
            url = urljoin(self.base_url, '/portal/login.html')
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.log_result("Login Styling", "FAIL", "Cannot access login page")
                return
            
            content = response.text
            
            # Check for styling elements that indicate proper centering
            styling_checks = {
                'login_container': r'class=["\'][^"\']*login-container[^"\']*["\']',
                'login_box': r'class=["\'][^"\']*login-box[^"\']*["\']',
                'flex_center': r'(display:\s*flex|justify-content:\s*center|align-items:\s*center)',
                'matrix_background': r'class=["\'][^"\']*matrix-background[^"\']*["\']'
            }
            
            found_styles = []
            for style_name, pattern in styling_checks.items():
                if re.search(pattern, content, re.IGNORECASE):
                    found_styles.append(style_name)
            
            if len(found_styles) >= 3:
                self.log_result("Login Styling", "PASS", 
                              f"Login styling elements found: {', '.join(found_styles)}")
            else:
                self.log_result("Login Styling", "WARN", 
                              f"Some styling elements missing: found {found_styles}")
                
        except requests.exceptions.RequestException as e:
            self.log_result("Login Styling", "FAIL", f"Error checking login styling: {str(e)}")
    
    def test_authentication_endpoints(self):
        """Test authentication API endpoints"""
        # Test /api/me endpoint (should return unauthenticated)
        try:
            url = urljoin(self.base_url, '/api/me')
            response = self.session.get(url)
            
            if response.status_code in [200, 401]:
                data = response.json()
                if data.get('authenticated') is False:
                    self.log_result("Auth Endpoint /api/me", "PASS", 
                                  "Correctly returns unauthenticated status")
                else:
                    self.log_result("Auth Endpoint /api/me", "WARN", 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Auth Endpoint /api/me", "FAIL", 
                              f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Auth Endpoint /api/me", "FAIL", f"Error testing /api/me: {str(e)}")
    
    def test_login_authentication(self):
        """Test login functionality with valid and invalid credentials"""
        # Test with invalid credentials
        try:
            url = urljoin(self.base_url, '/api/auth/login')
            invalid_creds = {
                'username': 'invalid_user',
                'password': 'invalid_password'
            }
            
            response = self.session.post(url, json=invalid_creds, 
                                       headers={'Content-Type': 'application/json'})
            
            if response.status_code in [200, 401, 403]:
                data = response.json()
                if data.get('success') is False:
                    self.log_result("Invalid Login Test", "PASS", 
                                  "Correctly rejects invalid credentials")
                else:
                    self.log_result("Invalid Login Test", "FAIL", 
                                  "Should reject invalid credentials")
            else:
                self.log_result("Invalid Login Test", "FAIL", 
                              f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Login Test", "FAIL", f"Error testing invalid login: {str(e)}")
        
        # Test with valid credentials (if available)
        for user_type, creds in self.test_users.items():
            try:
                url = urljoin(self.base_url, '/api/auth/login')
                response = self.session.post(url, json=creds,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') is True and 'user' in data:
                        self.log_result(f"Valid Login Test ({user_type})", "PASS", 
                                      f"Successfully authenticated {user_type}")
                        
                        # Test logout
                        logout_url = urljoin(self.base_url, '/api/auth/logout')
                        logout_response = self.session.post(logout_url)
                        if logout_response.status_code == 200:
                            self.log_result(f"Logout Test ({user_type})", "PASS", "Logout successful")
                        else:
                            self.log_result(f"Logout Test ({user_type})", "WARN", 
                                          f"Logout returned {logout_response.status_code}")
                    else:
                        self.log_result(f"Valid Login Test ({user_type})", "FAIL", 
                                      "Login response missing required fields")
                elif response.status_code == 401:
                    self.log_result(f"Valid Login Test ({user_type})", "WARN", 
                                  "User credentials not found in system (expected for test)")
                else:
                    self.log_result(f"Valid Login Test ({user_type})", "FAIL", 
                                  f"Login failed with status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Valid Login Test ({user_type})", "FAIL", 
                              f"Error testing valid login: {str(e)}")
    
    def test_portal_access_control(self):
        """Test that portal pages require authentication"""
        portal_pages = ['/portal/admin.html', '/portal/employee.html']
        
        for page in portal_pages:
            try:
                url = urljoin(self.base_url, page)
                response = self.session.get(url)
                
                if response.status_code == 200:
                    content = response.text
                    # Check if auth-check.js is loaded
                    if 'auth-check.js' in content:
                        self.log_result(f"Portal Access {page}", "PASS", 
                                      "Portal page includes auth check script")
                    else:
                        self.log_result(f"Portal Access {page}", "WARN", 
                                      "Portal page missing auth check script")
                else:
                    self.log_result(f"Portal Access {page}", "FAIL", 
                                  f"Cannot access portal page: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Portal Access {page}", "FAIL", 
                              f"Error testing portal access: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        try:
            url = urljoin(self.base_url, '/api/auth/login')
            invalid_creds = {'username': 'test_user', 'password': 'wrong_password'}
            
            # Make rapid requests to trigger rate limiting
            rate_limit_triggered = False
            for i in range(7):  # Try 7 requests (should trigger 5-request limit)
                response = self.session.post(url, json=invalid_creds,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 429 or (response.status_code == 200 and 
                    'too_many_attempts' in response.text):
                    rate_limit_triggered = True
                    break
                    
                time.sleep(0.1)  # Small delay between requests
            
            if rate_limit_triggered:
                self.log_result("Rate Limiting", "PASS", "Rate limiting is working")
            else:
                self.log_result("Rate Limiting", "WARN", 
                              "Rate limiting not triggered (may need more attempts)")
                
        except Exception as e:
            self.log_result("Rate Limiting", "FAIL", f"Error testing rate limiting: {str(e)}")
    
    def test_security_headers(self):
        """Test security headers are present"""
        try:
            response = self.session.get(self.base_url)
            headers = response.headers
            
            security_headers = {
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff', 
                'X-XSS-Protection': '1; mode=block'
            }
            
            missing_headers = []
            for header, expected_value in security_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif expected_value and headers[header] != expected_value:
                    missing_headers.append(f"{header} (wrong value)")
            
            if not missing_headers:
                self.log_result("Security Headers", "PASS", "All security headers present")
            else:
                self.log_result("Security Headers", "WARN", 
                              f"Missing/incorrect headers: {', '.join(missing_headers)}")
                
        except Exception as e:
            self.log_result("Security Headers", "FAIL", f"Error checking security headers: {str(e)}")
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        sql_payloads = [
            "' OR 1=1--",
            "'; DROP TABLE users--",
            "' UNION SELECT * FROM users--",
            "admin'/*"
        ]
        
        try:
            url = urljoin(self.base_url, '/api/auth/login')
            
            for payload in sql_payloads:
                test_data = {
                    'username': payload,
                    'password': 'test'
                }
                
                response = self.session.post(url, json=test_data,
                                           headers={'Content-Type': 'application/json'})
                
                # Should either reject with 400/403 or return authentication failure
                if response.status_code in [400, 403]:
                    self.log_result("SQL Injection Protection", "PASS", 
                                  f"Blocked SQL injection attempt: {payload[:20]}...")
                    break
                elif response.status_code == 200:
                    data = response.json()
                    if data.get('success') is False:
                        continue  # Normal auth failure, continue testing
                    else:
                        self.log_result("SQL Injection Protection", "FAIL", 
                                      f"SQL injection may have succeeded: {payload}")
                        return
            else:
                self.log_result("SQL Injection Protection", "PASS", 
                              "SQL injection attempts properly handled")
                
        except Exception as e:
            self.log_result("SQL Injection Protection", "FAIL", 
                          f"Error testing SQL injection protection: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n🚀 Starting Matrica Networks Test Suite")
        print(f"Target URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Server connectivity
        self.test_server_connectivity()
        
        # UI and styling tests
        self.test_login_page_accessibility()
        self.test_css_files_loading()
        self.test_login_styling()
        
        # Authentication tests
        self.test_authentication_endpoints()
        self.test_login_authentication()
        self.test_portal_access_control()
        
        # Security tests
        self.test_rate_limiting()
        self.test_security_headers()
        self.test_sql_injection_protection()
        
        # Summary
        self.print_summary()
        
        # Save results if output file specified
        if self.output_file:
            self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"⚠ Warnings: {warnings}")
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['test']}: {result['message']}")
        
        if warnings > 0:
            print(f"\n⚠️  Warnings:")
            for result in self.results:
                if result['status'] == 'WARN':
                    print(f"  • {result['test']}: {result['message']}")
    
    def save_results(self):
        """Save results to JSON file"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'target_url': self.base_url,
                'total_tests': len(self.results),
                'passed': len([r for r in self.results if r['status'] == 'PASS']),
                'failed': len([r for r in self.results if r['status'] == 'FAIL']),
                'warnings': len([r for r in self.results if r['status'] == 'WARN']),
                'tests': self.results
            }
            
            with open(self.output_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"\n💾 Results saved to: {self.output_file}")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Matrica Networks Automation Test Suite')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Base URL to test (default: http://localhost:8000)')
    parser.add_argument('--output', help='Output JSON file for results')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run test suite
    test_suite = MatricaTestSuite(args.url, args.output)
    
    try:
        test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        test_suite.print_summary()
        if args.output:
            test_suite.save_results()
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        test_suite.print_summary()
        if args.output:
            test_suite.save_results()
        sys.exit(1)

if __name__ == '__main__':
    main()