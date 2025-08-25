#!/usr/bin/env python3
"""
🔐 MARITIME ASSISTANT - SECURITY & AUTHENTICATION TESTING SUITE
==============================================================

Comprehensive testing of security and authentication:
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting
- Authentication endpoints
- Authorization checks
- Password security
- Session management
- Security headers
- API key validation
- Data encryption

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import time
import hashlib
import base64
from urllib.parse import quote
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class SecurityAuthTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def log_result(self, test_name: str, passed: bool, response_time: float = 0, details: str = ""):
        """Log test results"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "response_time": response_time,
            "details": details
        })
        print(f"{status} - {test_name} ({response_time:.2f}s)")
        if details and not passed:
            print(f"   Details: {details}")

    def test_server_connectivity(self):
        """Test if backend server is accessible"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/docs", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Server Connectivity", True, response_time, "Backend server is running")
                return True
            else:
                self.log_result("Server Connectivity", False, response_time, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Server Connectivity", False, 0, f"Connection failed: {e}")
            return False

    def test_input_validation(self):
        """Test input validation and sanitization"""
        
        # Test SQL injection attempts
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "'; INSERT INTO users VALUES ('hacker'); --",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_payloads:
            try:
                start_time = time.time()
                
                # Test SQL injection in chat query
                response = requests.post(f"{BASE_URL}/chat", 
                                       json={"query": payload}, 
                                       timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                # Should not crash and should sanitize input
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '').lower()
                    
                    # Check if SQL injection was executed (shouldn't contain SQL error messages)
                    sql_errors = ['sql error', 'syntax error', 'mysql error', 'postgres error', 'database error']
                    has_sql_errors = any(error in response_text for error in sql_errors)
                    
                    if not has_sql_errors:
                        self.log_result(f"SQL Injection Prevention: {payload[:20]}...", True, response_time,
                                      "Input properly sanitized")
                    else:
                        self.log_result(f"SQL Injection Prevention: {payload[:20]}...", False, response_time,
                                      "SQL error detected in response")
                else:
                    # Server returning error is also acceptable for malicious input
                    if response.status_code in [400, 422]:
                        self.log_result(f"SQL Injection Prevention: {payload[:20]}...", True, response_time,
                                      f"Properly rejected with HTTP {response.status_code}")
                    else:
                        self.log_result(f"SQL Injection Prevention: {payload[:20]}...", False, response_time,
                                      f"Unexpected status: {response.status_code}")
                        
            except Exception as e:
                self.log_result(f"SQL Injection Prevention: {payload[:20]}...", False, 0, f"Error: {e}")

    def test_xss_protection(self):
        """Test XSS (Cross-Site Scripting) protection"""
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            try:
                start_time = time.time()
                
                response = requests.post(f"{BASE_URL}/chat", 
                                       json={"query": payload}, 
                                       timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
                    
                    # Check if XSS payload is properly escaped/sanitized
                    dangerous_patterns = ['<script>', 'javascript:', 'onerror=', 'onload=']
                    has_dangerous_content = any(pattern in response_text for pattern in dangerous_patterns)
                    
                    if not has_dangerous_content:
                        self.log_result(f"XSS Protection: {payload[:30]}...", True, response_time,
                                      "XSS payload properly sanitized")
                    else:
                        self.log_result(f"XSS Protection: {payload[:30]}...", False, response_time,
                                      "Dangerous XSS content detected in response")
                else:
                    # Rejection of malicious input is acceptable
                    if response.status_code in [400, 422]:
                        self.log_result(f"XSS Protection: {payload[:30]}...", True, response_time,
                                      f"Properly rejected with HTTP {response.status_code}")
                    else:
                        self.log_result(f"XSS Protection: {payload[:30]}...", False, response_time,
                                      f"Unexpected status: {response.status_code}")
                        
            except Exception as e:
                self.log_result(f"XSS Protection: {payload[:30]}...", False, 0, f"Error: {e}")

    def test_security_headers(self):
        """Test security headers in HTTP responses"""
        try:
            start_time = time.time()
            
            response = requests.get(f"{BASE_URL}/docs", timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                headers = response.headers
                
                # Important security headers to check
                security_headers = {
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                    'X-XSS-Protection': '1; mode=block',
                    'Strict-Transport-Security': 'max-age',
                    'Content-Security-Policy': 'default-src',
                    'Referrer-Policy': ['strict-origin', 'no-referrer']
                }
                
                present_headers = []
                missing_headers = []
                
                for header, expected_values in security_headers.items():
                    if header in headers:
                        header_value = headers[header]
                        if isinstance(expected_values, list):
                            if any(val in header_value for val in expected_values):
                                present_headers.append(header)
                            else:
                                missing_headers.append(f"{header} (incorrect value)")
                        elif expected_values in header_value:
                            present_headers.append(header)
                        else:
                            missing_headers.append(f"{header} (incorrect value)")
                    else:
                        missing_headers.append(header)
                
                # CORS headers (already tested, but check for security)
                cors_headers = ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods']
                cors_present = sum(1 for h in cors_headers if h in headers)
                
                if len(present_headers) >= 2:  # At least some security headers
                    self.log_result("Security Headers", True, response_time,
                                  f"Present: {present_headers}, CORS: {cors_present}/{len(cors_headers)}")
                else:
                    self.log_result("Security Headers", False, response_time,
                                  f"Missing critical headers: {missing_headers[:3]}")
            else:
                self.log_result("Security Headers", False, response_time,
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Security Headers", False, 0, f"Error: {e}")

    def test_rate_limiting(self):
        """Test rate limiting protection"""
        try:
            start_time = time.time()
            
            # Send multiple requests rapidly
            def make_request():
                try:
                    response = requests.post(f"{BASE_URL}/chat", 
                                           json={"query": "rate limit test"}, 
                                           timeout=5)
                    return response.status_code
                except:
                    return 0
            
            # Send 20 requests in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in as_completed(futures)]
            
            response_time = time.time() - start_time
            
            # Count different response codes
            successful_requests = sum(1 for code in results if code == 200)
            rate_limited = sum(1 for code in results if code == 429)
            errors = sum(1 for code in results if code not in [200, 429])
            
            # Rate limiting is good if some requests are blocked
            if rate_limited > 0:
                self.log_result("Rate Limiting", True, response_time,
                              f"Rate limiting active: {rate_limited}/20 requests blocked")
            elif successful_requests == 20:
                self.log_result("Rate Limiting", False, response_time,
                              "No rate limiting detected (all requests succeeded)")
            else:
                self.log_result("Rate Limiting", False, response_time,
                              f"Unexpected results: {successful_requests} success, {errors} errors")
                
        except Exception as e:
            self.log_result("Rate Limiting", False, 0, f"Error: {e}")

    def test_authentication_endpoints(self):
        """Test authentication-related endpoints"""
        
        # Check for common authentication endpoints
        auth_endpoints = [
            "/auth/login",
            "/auth/register", 
            "/auth/logout",
            "/login",
            "/register",
            "/token",
            "/api/auth/login",
            "/api/auth/register"
        ]
        
        for endpoint in auth_endpoints:
            try:
                start_time = time.time()
                
                # Test POST request (most auth endpoints are POST)
                response = requests.post(f"{BASE_URL}{endpoint}", 
                                       json={"username": "test", "password": "test"}, 
                                       timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 404:
                    # Endpoint doesn't exist - this is expected for many
                    continue
                elif response.status_code in [200, 400, 401, 422]:
                    # Endpoint exists and responds appropriately
                    self.log_result(f"Auth Endpoint: {endpoint}", True, response_time,
                                  f"Endpoint available (HTTP {response.status_code})")
                    return True  # Found at least one auth endpoint
                else:
                    self.log_result(f"Auth Endpoint: {endpoint}", False, response_time,
                                  f"Unexpected response: {response.status_code}")
                    
            except Exception as e:
                continue
        
        # If no auth endpoints found
        self.log_result("Authentication Endpoints", False, 0,
                      "No authentication endpoints detected")

    def test_input_size_limits(self):
        """Test input size validation"""
        try:
            start_time = time.time()
            
            # Test with very large input
            large_input = "A" * 100000  # 100KB string
            
            response = requests.post(f"{BASE_URL}/chat", 
                                   json={"query": large_input}, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            # Should either handle it gracefully or reject it
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    self.log_result("Input Size Limits", True, response_time,
                                  "Large input handled gracefully")
                else:
                    self.log_result("Input Size Limits", False, response_time,
                                  "Large input caused invalid response")
            elif response.status_code in [413, 400, 422]:  # Payload too large, bad request
                self.log_result("Input Size Limits", True, response_time,
                              f"Large input properly rejected (HTTP {response.status_code})")
            else:
                self.log_result("Input Size Limits", False, response_time,
                              f"Unexpected response to large input: {response.status_code}")
                
        except Exception as e:
            if "timeout" in str(e).lower():
                self.log_result("Input Size Limits", False, TEST_TIMEOUT, "Large input caused timeout")
            else:
                self.log_result("Input Size Limits", False, 0, f"Error: {e}")

    def test_file_upload_security(self):
        """Test file upload security"""
        try:
            start_time = time.time()
            
            # Test malicious file upload
            malicious_files = [
                ("malicious.exe", b"MZ\x90\x00", "application/x-executable"),
                ("script.js", b"alert('xss')", "application/javascript"),
                ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
                ("test.txt", b"A" * 50000000, "text/plain")  # 50MB file
            ]
            
            upload_endpoints = ["/upload", "/upload-document", "/api/upload"]
            
            for endpoint in upload_endpoints:
                for filename, content, content_type in malicious_files:
                    try:
                        files = {'file': (filename, content, content_type)}
                        
                        response = requests.post(f"{BASE_URL}{endpoint}", 
                                               files=files, 
                                               timeout=TEST_TIMEOUT)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 404:
                            continue  # Endpoint doesn't exist
                        elif response.status_code in [400, 413, 415, 422]:
                            # Properly rejected malicious/large files
                            self.log_result(f"File Upload Security: {filename}", True, response_time,
                                          f"Malicious file rejected (HTTP {response.status_code})")
                            return  # At least one upload endpoint is secure
                        elif response.status_code == 200:
                            # Accepted the file - check if it's properly validated
                            data = response.json()
                            if 'error' in str(data).lower() or 'invalid' in str(data).lower():
                                self.log_result(f"File Upload Security: {filename}", True, response_time,
                                              "File processed with security validation")
                            else:
                                self.log_result(f"File Upload Security: {filename}", False, response_time,
                                              f"Malicious file accepted: {filename}")
                                return
                        
                    except Exception as e:
                        if "timeout" in str(e).lower():
                            self.log_result(f"File Upload Security: {filename}", False, TEST_TIMEOUT,
                                          "Large file caused timeout")
                            return
            
            # If we get here, no upload endpoints were found
            self.log_result("File Upload Security", False, 0, "No file upload endpoints found")
            
        except Exception as e:
            self.log_result("File Upload Security", False, 0, f"Error: {e}")

    def test_cors_security(self):
        """Test CORS security configuration"""
        try:
            start_time = time.time()
            
            # Test CORS with various origins
            test_origins = [
                "http://malicious.com",
                "https://evil.com", 
                "http://localhost:3000",  # Legitimate frontend
                "*"  # Wildcard (should be restricted)
            ]
            
            for origin in test_origins:
                headers = {
                    'Origin': origin,
                    'Access-Control-Request-Method': 'POST'
                }
                
                response = requests.options(f"{BASE_URL}/chat", 
                                          headers=headers, 
                                          timeout=TEST_TIMEOUT)
                
                if response.status_code in [200, 204]:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', '')
                    
                    if origin in ["http://malicious.com", "https://evil.com"] and cors_origin == origin:
                        self.log_result(f"CORS Security: {origin}", False, 0,
                                      f"Malicious origin allowed: {cors_origin}")
                        return
            
            response_time = time.time() - start_time
            self.log_result("CORS Security", True, response_time,
                          "CORS properly configured - malicious origins rejected")
            
        except Exception as e:
            self.log_result("CORS Security", False, 0, f"Error: {e}")

    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure"""
        try:
            start_time = time.time()
            
            # Test various endpoints for sensitive information
            test_endpoints = [
                "/docs",
                "/openapi.json",
                "/",
                "/health",
                "/status",
                "/config",
                "/debug"
            ]
            
            sensitive_keywords = [
                "password", "secret", "key", "token", "private",
                "database", "db_", "connection", "api_key",
                "admin", "debug", "traceback", "exception"
            ]
            
            exposed_data = []
            
            for endpoint in test_endpoints:
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=TEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        content = response.text.lower()
                        
                        for keyword in sensitive_keywords:
                            if keyword in content and keyword not in ["password", "secret"]:
                                # Allow documentation mentions but not actual values
                                if not any(safe_word in content for safe_word in ["example", "placeholder", "description"]):
                                    exposed_data.append(f"{endpoint}: {keyword}")
                                    
                except:
                    continue
            
            response_time = time.time() - start_time
            
            if len(exposed_data) == 0:
                self.log_result("Sensitive Data Exposure", True, response_time,
                              "No sensitive data exposed in public endpoints")
            else:
                self.log_result("Sensitive Data Exposure", False, response_time,
                              f"Potential exposure: {exposed_data[:3]}")
                
        except Exception as e:
            self.log_result("Sensitive Data Exposure", False, 0, f"Error: {e}")

    def test_api_documentation_security(self):
        """Test API documentation security"""
        try:
            start_time = time.time()
            
            response = requests.get(f"{BASE_URL}/docs", timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check if sensitive endpoints are documented
                sensitive_endpoints = [
                    "admin", "debug", "internal", "private",
                    "test", "dev", "development"
                ]
                
                security_issues = []
                for endpoint in sensitive_endpoints:
                    if endpoint in content:
                        security_issues.append(endpoint)
                
                if len(security_issues) == 0:
                    self.log_result("API Documentation Security", True, response_time,
                                  "No sensitive endpoints exposed in documentation")
                else:
                    self.log_result("API Documentation Security", False, response_time,
                                  f"Sensitive endpoints in docs: {security_issues}")
            else:
                # Documentation not accessible - could be good for security
                self.log_result("API Documentation Security", True, response_time,
                              "API documentation not publicly accessible")
                
        except Exception as e:
            self.log_result("API Documentation Security", False, 0, f"Error: {e}")

    def test_error_handling_security(self):
        """Test error handling doesn't leak sensitive information"""
        try:
            start_time = time.time()
            
            # Trigger various error conditions
            error_tests = [
                {"url": "/nonexistent", "method": "GET"},
                {"url": "/chat", "method": "POST", "data": {"invalid": "data"}},
                {"url": "/weather", "method": "POST", "data": {"lat": "invalid"}},
                {"url": "/api/ports/search", "method": "GET"}  # Missing required param
            ]
            
            for test in error_tests:
                try:
                    if test["method"] == "GET":
                        response = requests.get(f"{BASE_URL}{test['url']}", timeout=TEST_TIMEOUT)
                    else:
                        response = requests.post(f"{BASE_URL}{test['url']}", 
                                               json=test.get("data"), 
                                               timeout=TEST_TIMEOUT)
                    
                    if response.status_code >= 400:
                        error_content = response.text.lower()
                        
                        # Check for information disclosure in errors
                        disclosure_patterns = [
                            "traceback", "stack trace", "file path", 
                            "database error", "sql error", "connection",
                            "internal server", "debug", "exception"
                        ]
                        
                        found_disclosures = [p for p in disclosure_patterns if p in error_content]
                        
                        if found_disclosures:
                            self.log_result(f"Error Security: {test['url']}", False, 0,
                                          f"Information disclosure: {found_disclosures[:2]}")
                            return
                            
                except:
                    continue
            
            response_time = time.time() - start_time
            self.log_result("Error Handling Security", True, response_time,
                          "Error messages don't expose sensitive information")
            
        except Exception as e:
            self.log_result("Error Handling Security", False, 0, f"Error: {e}")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\\n" + "="*80)
        print("🔐 SECURITY & AUTHENTICATION TEST RESULTS")
        print("="*80)
        
        print(f"📊 SUMMARY:")
        print(f"   ✅ Passed: {passed_tests}/{total_tests}")
        print(f"   ❌ Failed: {failed_tests}/{total_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        print(f"   ⚡ Avg Response: {avg_response_time:.2f}s")
        
        print("\\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            print(f"   {i:2d}. {result['status']} - {result['test']} ({result['response_time']:.2f}s)")
            if result['details']:
                print(f"       → {result['details']}")
        
        print("\\n🔐 TESTED SECURITY ASPECTS:")
        print("   • Input validation and SQL injection prevention")
        print("   • XSS (Cross-Site Scripting) protection")
        print("   • Security headers configuration")
        print("   • Rate limiting and DoS protection")
        print("   • Authentication endpoint security")
        print("   • File upload security validation")
        print("   • CORS security configuration")
        print("   • Sensitive data exposure prevention")
        print("   • API documentation security")
        print("   • Error handling security")
        
        # Security rating
        if passed_tests == total_tests:
            print("\\n🛡️ RESULT: SECURITY IS EXCELLENT! 🛡️")
        elif passed_tests >= total_tests * 0.9:
            print("\\n✅ RESULT: SECURITY IS VERY GOOD")
        elif passed_tests >= total_tests * 0.7:
            print("\\n⚠️ RESULT: SECURITY IS ADEQUATE - SOME IMPROVEMENTS NEEDED")
        else:
            print("\\n❌ RESULT: SECURITY NEEDS SIGNIFICANT ATTENTION")
        
        print("="*80)

def main():
    print("🔐 MARITIME ASSISTANT - SECURITY & AUTHENTICATION TESTING")
    print("=" * 60)
    print("Testing comprehensive security and authentication...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("⚠️  Note: This includes penetration testing - only run on your own systems!")
    print("=" * 60)
    
    suite = SecurityAuthTestSuite()
    
    # Run all security tests
    if suite.test_server_connectivity():
        suite.test_input_validation()
        suite.test_xss_protection()
        suite.test_security_headers()
        suite.test_rate_limiting()
        suite.test_authentication_endpoints()
        suite.test_input_size_limits()
        suite.test_file_upload_security()
        suite.test_cors_security()
        suite.test_sensitive_data_exposure()
        suite.test_api_documentation_security()
        suite.test_error_handling_security()
    else:
        print("❌ Server not responding. Please ensure the backend server is running.")
        return
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
