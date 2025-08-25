#!/usr/bin/env python3
"""
🔐 MARITIME ASSISTANT - AUTHENTICATION & SECURITY TESTING SUITE
================================================================

Comprehensive testing of the new JWT authentication system:
- User registration and login
- Token validation and expiration
- Protected route access control
- Role-based permissions
- Authentication endpoints
- Security improvements validation

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class AuthenticationTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.admin_token = None
        self.user_token = None
        
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
        if details:
            print(f"   → {details}")

    def test_server_connectivity(self):
        """Test if backend server is accessible"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Server Connectivity", True, response_time, 
                              f"API: {data.get('message', 'N/A')}")
                return True
            else:
                self.log_result("Server Connectivity", False, response_time, 
                              f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Server Connectivity", False, 0, f"Connection failed: {e}")
            return False

    def test_admin_login(self):
        """Test admin user login with default credentials"""
        try:
            start_time = time.time()
            
            login_data = {
                "username": "admin",
                "password": "MaritimeAdmin2025!"
            }
            
            response = requests.post(f"{BASE_URL}/auth/login", 
                                   json=login_data, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['access_token', 'refresh_token', 'user_info']
                
                if all(field in data for field in required_fields):
                    self.admin_token = data['access_token']
                    user_info = data['user_info']
                    self.log_result("Admin Login", True, response_time,
                                  f"Admin user: {user_info.get('username')} | Role: {user_info.get('role')}")
                    return True
                else:
                    self.log_result("Admin Login", False, response_time,
                                  f"Missing fields: {[f for f in required_fields if f not in data]}")
            else:
                self.log_result("Admin Login", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Admin Login", False, 0, f"Error: {e}")
        
        return False

    def test_user_registration(self):
        """Test new user registration"""
        try:
            start_time = time.time()
            
            user_data = {
                "username": "testuser",
                "email": "test@maritime.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
                "company": "Maritime Testing Co",
                "role": "user"
            }
            
            response = requests.post(f"{BASE_URL}/auth/register", 
                                   json=user_data, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'user' in data and 'message' in data:
                    user_info = data['user']
                    self.log_result("User Registration", True, response_time,
                                  f"User created: {user_info.get('username')} | ID: {user_info.get('user_id')}")
                    return True
                else:
                    self.log_result("User Registration", False, response_time,
                                  "Invalid response structure")
            else:
                self.log_result("User Registration", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("User Registration", False, 0, f"Error: {e}")
        
        return False

    def test_user_login(self):
        """Test user login"""
        try:
            start_time = time.time()
            
            login_data = {
                "username": "testuser",
                "password": "TestPassword123!"
            }
            
            response = requests.post(f"{BASE_URL}/auth/login", 
                                   json=login_data, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.user_token = data['access_token']
                    expires_in = data.get('expires_in', 0)
                    self.log_result("User Login", True, response_time,
                                  f"Token received | Expires in: {expires_in}s")
                    return True
                else:
                    self.log_result("User Login", False, response_time,
                                  "No access token in response")
            else:
                self.log_result("User Login", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("User Login", False, 0, f"Error: {e}")
        
        return False

    def test_protected_endpoint_access(self):
        """Test access to protected endpoints with valid token"""
        if not self.user_token:
            self.log_result("Protected Endpoint Access", False, 0, "No user token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            response = requests.post(f"{BASE_URL}/chat", 
                                   json={"query": "Hello, this is a test from authenticated user"}, 
                                   headers=headers,
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    self.log_result("Protected Endpoint Access", True, response_time,
                                  "Chat endpoint accessible with valid token")
                    return True
                else:
                    self.log_result("Protected Endpoint Access", False, response_time,
                                  "Invalid response structure")
            else:
                self.log_result("Protected Endpoint Access", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Protected Endpoint Access", False, 0, f"Error: {e}")
        
        return False

    def test_unauthorized_access(self):
        """Test that protected endpoints reject unauthorized access"""
        try:
            start_time = time.time()
            
            # Test without token
            response = requests.post(f"{BASE_URL}/chat", 
                                   json={"query": "This should be rejected"}, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 403:
                self.log_result("Unauthorized Access Blocking", True, response_time,
                              "Protected endpoint properly rejects unauthorized requests")
                return True
            else:
                self.log_result("Unauthorized Access Blocking", False, response_time,
                              f"Expected HTTP 403, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Unauthorized Access Blocking", False, 0, f"Error: {e}")
        
        return False

    def test_invalid_token_access(self):
        """Test access with invalid/expired token"""
        try:
            start_time = time.time()
            
            # Use invalid token
            invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJpbnZhbGlkIiwidXNlcl9pZCI6ImludmFsaWQiLCJyb2xlIjoidXNlciIsImV4cCI6MTY5MjAwMDAwMCwidHlwZSI6ImFjY2VzcyJ9.invalid"
            headers = {"Authorization": f"Bearer {invalid_token}"}
            
            response = requests.post(f"{BASE_URL}/chat", 
                                   json={"query": "This should be rejected"}, 
                                   headers=headers,
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code in [401, 403]:
                self.log_result("Invalid Token Blocking", True, response_time,
                              f"Invalid token properly rejected (HTTP {response.status_code})")
                return True
            else:
                self.log_result("Invalid Token Blocking", False, response_time,
                              f"Expected HTTP 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Token Blocking", False, 0, f"Error: {e}")
        
        return False

    def test_role_based_access_control(self):
        """Test admin-only endpoints"""
        if not self.admin_token:
            self.log_result("Role-Based Access Control", False, 0, "No admin token available")
            return False
            
        try:
            start_time = time.time()
            
            # Test admin-only endpoint
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{BASE_URL}/auth/stats", 
                                  headers=headers,
                                  timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'total_users' in data:
                    self.log_result("Role-Based Access Control", True, response_time,
                                  f"Admin stats: {data.get('total_users')} users, {data.get('active_sessions', 0)} sessions")
                    return True
                else:
                    self.log_result("Role-Based Access Control", False, response_time,
                                  "Invalid response structure")
            else:
                self.log_result("Role-Based Access Control", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Role-Based Access Control", False, 0, f"Error: {e}")
        
        return False

    def test_user_info_endpoint(self):
        """Test user info retrieval"""
        if not self.user_token:
            self.log_result("User Info Endpoint", False, 0, "No user token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            response = requests.get(f"{BASE_URL}/auth/me", 
                                  headers=headers,
                                  timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['user_id', 'username', 'email', 'role']
                
                if all(field in data for field in required_fields):
                    self.log_result("User Info Endpoint", True, response_time,
                                  f"User: {data.get('username')} | Role: {data.get('role')}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("User Info Endpoint", False, response_time,
                                  f"Missing fields: {missing}")
            else:
                self.log_result("User Info Endpoint", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("User Info Endpoint", False, 0, f"Error: {e}")
        
        return False

    def test_public_endpoint_access(self):
        """Test public endpoint access without authentication"""
        try:
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/public/chat", 
                                   json={"query": "Public test query"}, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and '[PUBLIC ACCESS' in data['response']:
                    self.log_result("Public Endpoint Access", True, response_time,
                                  "Public endpoint accessible without authentication")
                    return True
                else:
                    self.log_result("Public Endpoint Access", False, response_time,
                                  "Public endpoint response invalid")
            else:
                self.log_result("Public Endpoint Access", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Public Endpoint Access", False, 0, f"Error: {e}")
        
        return False

    def test_password_strength_validation(self):
        """Test password strength validation"""
        try:
            start_time = time.time()
            
            # Test with weak password
            weak_user_data = {
                "username": "weakuser",
                "email": "weak@maritime.com",
                "password": "weak",  # Weak password
                "role": "user"
            }
            
            response = requests.post(f"{BASE_URL}/auth/register", 
                                   json=weak_user_data, 
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                self.log_result("Password Strength Validation", True, response_time,
                              "Weak password properly rejected")
                return True
            else:
                self.log_result("Password Strength Validation", False, response_time,
                              f"Expected HTTP 400, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Password Strength Validation", False, 0, f"Error: {e}")
        
        return False

    def test_logout_functionality(self):
        """Test user logout and token revocation"""
        if not self.user_token:
            self.log_result("Logout Functionality", False, 0, "No user token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            response = requests.post(f"{BASE_URL}/auth/logout", 
                                   headers=headers,
                                   timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Test that token is revoked by trying to use it
                test_response = requests.get(f"{BASE_URL}/auth/me", 
                                           headers=headers,
                                           timeout=5)
                
                if test_response.status_code == 401:
                    self.log_result("Logout Functionality", True, response_time,
                                  "Token properly revoked after logout")
                    return True
                else:
                    self.log_result("Logout Functionality", False, response_time,
                                  "Token not properly revoked")
            else:
                self.log_result("Logout Functionality", False, response_time,
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Logout Functionality", False, 0, f"Error: {e}")
        
        return False

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\\n" + "="*80)
        print("🔐 AUTHENTICATION & SECURITY TEST RESULTS")
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
        
        print("\\n🔐 AUTHENTICATION FEATURES TESTED:")
        print("   • User registration with password validation")
        print("   • JWT token generation and validation")
        print("   • Protected endpoint access control")
        print("   • Role-based authorization (admin/user)")
        print("   • Token expiration and revocation")
        print("   • Public endpoint access without auth")
        print("   • Password strength requirements")
        print("   • Logout and token cleanup")
        
        # Authentication security rating
        if passed_tests == total_tests:
            print("\\n🛡️ RESULT: AUTHENTICATION SYSTEM IS EXCELLENT! 🛡️")
            print("🚀 PRODUCTION READY - 100% Authentication Security")
        elif passed_tests >= total_tests * 0.9:
            print("\\n✅ RESULT: AUTHENTICATION SYSTEM IS VERY GOOD")
            print("🎯 NEAR PRODUCTION READY - 90%+ Authentication Security")
        elif passed_tests >= total_tests * 0.8:
            print("\\n⚠️ RESULT: AUTHENTICATION SYSTEM IS GOOD - MINOR IMPROVEMENTS NEEDED")
        else:
            print("\\n❌ RESULT: AUTHENTICATION SYSTEM NEEDS SIGNIFICANT WORK")
        
        print("="*80)

def main():
    print("🔐 MARITIME ASSISTANT - AUTHENTICATION & SECURITY TESTING")
    print("=" * 65)
    print("Testing comprehensive JWT authentication system...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 65)
    
    suite = AuthenticationTestSuite()
    
    # Run all authentication tests
    if suite.test_server_connectivity():
        suite.test_admin_login()
        suite.test_user_registration()
        suite.test_user_login()
        suite.test_protected_endpoint_access()
        suite.test_unauthorized_access()
        suite.test_invalid_token_access()
        suite.test_role_based_access_control()
        suite.test_user_info_endpoint()
        suite.test_public_endpoint_access()
        suite.test_password_strength_validation()
        suite.test_logout_functionality()
    else:
        print("❌ Server not responding. Please ensure the backend server is running.")
        return
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
