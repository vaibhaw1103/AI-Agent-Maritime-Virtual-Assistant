#!/usr/bin/env python3
"""
🚢 MARITIME ASSISTANT - END-TO-END INTEGRATION TESTING
=====================================================

Comprehensive workflow testing simulating real user journeys:
1. User registration and authentication flow
2. Weather data retrieval workflows
3. Port information access patterns
4. AI assistant interaction flows
5. Multi-user concurrent workflows
6. Error handling and recovery
7. Security boundary testing
8. Complete system integration validation

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class IntegrationTestSuite:
    """End-to-end integration testing suite"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.users = {}  # Store user sessions
        self.test_data = {
            'locations': [
                {'name': 'Singapore', 'lat': 1.3521, 'lon': 103.8198},
                {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
                {'name': 'Rotterdam', 'lat': 51.9225, 'lon': 4.47917},
                {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060},
            ],
            'ports': ['singapore', 'mumbai', 'rotterdam', 'shanghai', 'hamburg'],
            'queries': [
                'What is the current weather in Singapore?',
                'Tell me about port conditions in Mumbai',
                'What are the maritime regulations for shipping?',
                'How do tides affect port operations?'
            ]
        }
        
    def log_result(self, workflow: str, step: str, passed: bool, duration: float = 0, details: str = ""):
        """Log integration test results"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results.append({
            "workflow": workflow,
            "step": step,
            "status": status,
            "passed": passed,
            "duration": duration,
            "details": details
        })
        print(f"  {status} - {step} ({duration:.2f}s)")
        if details:
            print(f"    → {details}")

    def test_user_registration_workflow(self):
        """Test complete user registration and profile setup workflow"""
        print(f"\\n👤 TESTING USER REGISTRATION WORKFLOW...")
        
        # Step 1: Register new user
        user_data = {
            "username": f"test_captain_{int(time.time())}",
            "email": f"captain{int(time.time())}@maritime.com",
            "password": "SecureMaritime2025!",
            "full_name": "Captain Test User",
            "company": "Maritime Testing Co",
            "role": "user"
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=TEST_TIMEOUT)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                registration_data = response.json()
                self.log_result("User Registration", "Register New User", True, duration,
                              f"User ID: {registration_data['user']['user_id']}")
                
                # Step 2: Login with new user
                login_data = {"username": user_data["username"], "password": user_data["password"]}
                start_time = time.time()
                login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=TEST_TIMEOUT)
                duration = time.time() - start_time
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    user_token = login_result['access_token']
                    self.users[user_data["username"]] = {
                        'token': user_token,
                        'user_info': login_result['user_info'],
                        'registration_data': registration_data
                    }
                    
                    self.log_result("User Registration", "Login After Registration", True, duration,
                                  f"Token received, expires in {login_result['expires_in']}s")
                    
                    # Step 3: Verify user profile access
                    start_time = time.time()
                    headers = {"Authorization": f"Bearer {user_token}"}
                    profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=TEST_TIMEOUT)
                    duration = time.time() - start_time
                    
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        self.log_result("User Registration", "Profile Access", True, duration,
                                      f"Profile: {profile_data['full_name']} | Role: {profile_data['role']}")
                        return True
                    else:
                        self.log_result("User Registration", "Profile Access", False, duration,
                                      f"Profile access failed: {profile_response.status_code}")
                else:
                    self.log_result("User Registration", "Login After Registration", False, duration,
                                  f"Login failed: {login_response.status_code}")
            else:
                self.log_result("User Registration", "Register New User", False, duration,
                              f"Registration failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("User Registration", "Registration Workflow", False, 0, f"Error: {e}")
        
        return False

    def test_weather_data_workflow(self):
        """Test complete weather data retrieval workflow"""
        print(f"\\n🌦️ TESTING WEATHER DATA WORKFLOW...")
        
        # Get a user token for authenticated requests
        user_token = None
        if self.users:
            user_token = list(self.users.values())[0]['token']
        
        # Step 1: Test coordinate-based weather
        for location in self.test_data['locations']:
            try:
                start_time = time.time()
                weather_request = {
                    "latitude": location['lat'],
                    "longitude": location['lon'],
                    "location_name": location['name']
                }
                
                response = requests.post(f"{BASE_URL}/weather", json=weather_request, timeout=TEST_TIMEOUT)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    weather_data = response.json()
                    temp = weather_data.get('current_weather', {}).get('temperature', 'N/A')
                    conditions = weather_data.get('current_weather', {}).get('conditions', 'N/A')
                    
                    self.log_result("Weather Data", f"Coordinate Weather - {location['name']}", True, duration,
                                  f"Temperature: {temp}°C | Conditions: {conditions}")
                else:
                    self.log_result("Weather Data", f"Coordinate Weather - {location['name']}", False, duration,
                                  f"Weather request failed: {response.status_code}")
                    
            except Exception as e:
                self.log_result("Weather Data", f"Coordinate Weather - {location['name']}", False, 0, f"Error: {e}")
        
        # Step 2: Test port-based weather
        for port in self.test_data['ports'][:3]:  # Test first 3 ports
            try:
                start_time = time.time()
                response = requests.get(f"{BASE_URL}/port-weather/{port}", timeout=TEST_TIMEOUT)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    port_data = response.json()
                    port_name = port_data.get('port', {}).get('name', port)
                    weather = port_data.get('weather', {}).get('current_weather', {})
                    temp = weather.get('temperature', 'N/A')
                    
                    self.log_result("Weather Data", f"Port Weather - {port}", True, duration,
                                  f"Port: {port_name} | Temperature: {temp}°C")
                else:
                    self.log_result("Weather Data", f"Port Weather - {port}", False, duration,
                                  f"Port weather failed: {response.status_code}")
                    
            except Exception as e:
                self.log_result("Weather Data", f"Port Weather - {port}", False, 0, f"Error: {e}")

    def test_ai_assistant_workflow(self):
        """Test AI assistant interaction workflow"""
        print(f"\\n🤖 TESTING AI ASSISTANT WORKFLOW...")
        
        # Test both public and authenticated AI interactions
        
        # Step 1: Public AI interactions
        for query in self.test_data['queries'][:2]:  # Test first 2 queries
            try:
                start_time = time.time()
                response = requests.post(f"{BASE_URL}/public/chat", 
                                       json={"query": query}, timeout=TEST_TIMEOUT)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    ai_response = response.json()
                    response_text = ai_response.get('response', '')
                    confidence = ai_response.get('confidence', 0)
                    
                    self.log_result("AI Assistant", f"Public Query", True, duration,
                                  f"Query processed | Confidence: {confidence} | Response length: {len(response_text)}")
                else:
                    self.log_result("AI Assistant", f"Public Query", False, duration,
                                  f"Public AI failed: {response.status_code}")
                    
            except Exception as e:
                self.log_result("AI Assistant", f"Public Query", False, 0, f"Error: {e}")
        
        # Step 2: Authenticated AI interactions (if user available)
        if self.users:
            user_token = list(self.users.values())[0]['token']
            headers = {"Authorization": f"Bearer {user_token}"}
            
            for query in self.test_data['queries'][2:]:  # Test remaining queries
                try:
                    start_time = time.time()
                    response = requests.post(f"{BASE_URL}/chat", 
                                           json={"query": query}, 
                                           headers=headers, timeout=TEST_TIMEOUT)
                    duration = time.time() - start_time
                    
                    if response.status_code == 200:
                        ai_response = response.json()
                        response_text = ai_response.get('response', '')
                        
                        self.log_result("AI Assistant", f"Authenticated Query", True, duration,
                                      f"Authenticated query processed | Response length: {len(response_text)}")
                    else:
                        self.log_result("AI Assistant", f"Authenticated Query", False, duration,
                                      f"Authenticated AI failed: {response.status_code}")
                        
                except Exception as e:
                    self.log_result("AI Assistant", f"Authenticated Query", False, 0, f"Error: {e}")

    def test_multi_user_workflow(self):
        """Test multi-user concurrent workflow"""
        print(f"\\n👥 TESTING MULTI-USER WORKFLOW...")
        
        # Create additional test users
        additional_users = []
        for i in range(2):  # Create 2 additional users
            user_data = {
                "username": f"fleet_manager_{i}_{int(time.time())}",
                "email": f"manager{i}_{int(time.time())}@maritime.com",
                "password": "FleetManager2025!",
                "full_name": f"Fleet Manager {i+1}",
                "company": "Maritime Fleet Co",
                "role": "user"
            }
            
            try:
                # Register user
                reg_response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
                if reg_response.status_code == 200:
                    # Login user
                    login_response = requests.post(f"{BASE_URL}/auth/login", 
                                                 json={"username": user_data["username"], 
                                                      "password": user_data["password"]}, timeout=10)
                    if login_response.status_code == 200:
                        token = login_response.json()['access_token']
                        additional_users.append({
                            'username': user_data["username"],
                            'token': token,
                            'user_data': user_data
                        })
            except Exception:
                pass  # Continue with available users
        
        # Test concurrent operations
        def user_workflow(user_info, user_index):
            """Individual user workflow for concurrent testing"""
            results = []
            headers = {"Authorization": f"Bearer {user_info['token']}"}
            
            try:
                # Each user performs different operations
                if user_index == 0:
                    # User 1: Weather requests
                    response = requests.post(f"{BASE_URL}/weather", 
                                           json={"latitude": 1.35, "longitude": 103.82, "location_name": "Singapore"},
                                           headers=headers, timeout=10)
                    results.append(("Weather Request", response.status_code == 200))
                    
                elif user_index == 1:
                    # User 2: Port weather
                    response = requests.get(f"{BASE_URL}/port-weather/mumbai", timeout=10)
                    results.append(("Port Weather", response.status_code == 200))
                
                # Common operations: AI query
                response = requests.post(f"{BASE_URL}/chat",
                                       json={"query": f"User {user_index} maritime query"},
                                       headers=headers, timeout=10)
                results.append(("AI Query", response.status_code == 200))
                
                # Profile access
                response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
                results.append(("Profile Access", response.status_code == 200))
                
            except Exception as e:
                results.append(("Workflow Error", False))
            
            return results
        
        if additional_users:
            start_time = time.time()
            
            # Run concurrent user workflows
            threads = []
            thread_results = []
            
            for i, user in enumerate(additional_users):
                def run_user_workflow(u=user, idx=i):
                    result = user_workflow(u, idx)
                    thread_results.append((u['username'], result))
                
                thread = threading.Thread(target=run_user_workflow)
                thread.start()
                threads.append(thread)
            
            # Wait for all workflows to complete
            for thread in threads:
                thread.join(timeout=30)
            
            duration = time.time() - start_time
            
            # Analyze results
            total_operations = sum(len(results) for _, results in thread_results)
            successful_operations = sum(sum(1 for _, success in results if success) 
                                      for _, results in thread_results)
            
            success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
            
            if success_rate >= 80:
                self.log_result("Multi-User", "Concurrent User Operations", True, duration,
                              f"{len(additional_users)} users | {success_rate:.1f}% success rate")
            else:
                self.log_result("Multi-User", "Concurrent User Operations", False, duration,
                              f"{success_rate:.1f}% success rate - LOW")
        else:
            self.log_result("Multi-User", "User Creation", False, 0, "Could not create additional test users")

    def test_error_handling_workflow(self):
        """Test error handling and recovery workflow"""
        print(f"\\n🛡️ TESTING ERROR HANDLING WORKFLOW...")
        
        # Test various error conditions and recovery
        
        # Step 1: Invalid authentication
        try:
            start_time = time.time()
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.post(f"{BASE_URL}/chat", 
                                   json={"query": "This should fail"},
                                   headers=invalid_headers, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code in [401, 403]:
                self.log_result("Error Handling", "Invalid Token Rejection", True, duration,
                              f"Properly rejected with HTTP {response.status_code}")
            else:
                self.log_result("Error Handling", "Invalid Token Rejection", False, duration,
                              f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling", "Invalid Token Test", False, 0, f"Error: {e}")
        
        # Step 2: Invalid port request
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/port-weather/nonexistent_port_12345", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 404:
                self.log_result("Error Handling", "Invalid Port Request", True, duration,
                              "Properly returned 404 for invalid port")
            else:
                self.log_result("Error Handling", "Invalid Port Request", False, duration,
                              f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling", "Invalid Port Test", False, 0, f"Error: {e}")
        
        # Step 3: Malformed request handling
        try:
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/weather", 
                                   json={"invalid": "data"}, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code in [400, 422]:
                self.log_result("Error Handling", "Malformed Request", True, duration,
                              f"Properly handled malformed request with HTTP {response.status_code}")
            else:
                self.log_result("Error Handling", "Malformed Request", False, duration,
                              f"Unexpected handling: {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling", "Malformed Request Test", False, 0, f"Error: {e}")

    def test_complete_user_journey(self):
        """Test a complete real-world user journey"""
        print(f"\\n🚢 TESTING COMPLETE USER JOURNEY...")
        
        # Simulate a maritime professional's complete workflow
        journey_user = {
            "username": f"captain_journey_{int(time.time())}",
            "email": f"journey{int(time.time())}@shipping.com",
            "password": "CaptainJourney2025!",
            "full_name": "Captain Journey Test",
            "company": "Global Shipping Ltd",
            "role": "user"
        }
        
        try:
            # Journey Step 1: Register and login
            start_time = time.time()
            reg_response = requests.post(f"{BASE_URL}/auth/register", json=journey_user, timeout=15)
            
            if reg_response.status_code == 200:
                login_response = requests.post(f"{BASE_URL}/auth/login", 
                                             json={"username": journey_user["username"], 
                                                  "password": journey_user["password"]}, timeout=15)
                
                if login_response.status_code == 200:
                    token = login_response.json()['access_token']
                    headers = {"Authorization": f"Bearer {token}"}
                    setup_duration = time.time() - start_time
                    
                    self.log_result("User Journey", "Account Setup & Login", True, setup_duration,
                                  "User registered and authenticated successfully")
                    
                    # Journey Step 2: Check weather for departure port
                    start_time = time.time()
                    departure_weather = requests.post(f"{BASE_URL}/weather",
                                                    json={"latitude": 1.35, "longitude": 103.82, "location_name": "Singapore"},
                                                    headers=headers, timeout=15)
                    weather_duration = time.time() - start_time
                    
                    if departure_weather.status_code == 200:
                        self.log_result("User Journey", "Departure Weather Check", True, weather_duration,
                                      "Weather data retrieved for departure planning")
                    else:
                        self.log_result("User Journey", "Departure Weather Check", False, weather_duration,
                                      "Weather check failed")
                    
                    # Journey Step 3: Check destination port conditions
                    start_time = time.time()
                    port_response = requests.get(f"{BASE_URL}/port-weather/mumbai", timeout=15)
                    port_duration = time.time() - start_time
                    
                    if port_response.status_code == 200:
                        self.log_result("User Journey", "Destination Port Check", True, port_duration,
                                      "Port conditions retrieved for arrival planning")
                    else:
                        self.log_result("User Journey", "Destination Port Check", False, port_duration,
                                      "Port check failed")
                    
                    # Journey Step 4: Ask AI for maritime advice
                    start_time = time.time()
                    ai_query = "What are the best practices for shipping from Singapore to Mumbai during monsoon season?"
                    ai_response = requests.post(f"{BASE_URL}/chat",
                                              json={"query": ai_query},
                                              headers=headers, timeout=20)
                    ai_duration = time.time() - start_time
                    
                    if ai_response.status_code == 200:
                        advice = ai_response.json().get('response', '')
                        self.log_result("User Journey", "Maritime Consultation", True, ai_duration,
                                      f"AI advice received: {len(advice)} characters")
                    else:
                        self.log_result("User Journey", "Maritime Consultation", False, ai_duration,
                                      "AI consultation failed")
                    
                    # Journey Step 5: Update profile and logout
                    start_time = time.time()
                    profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
                    
                    if profile_response.status_code == 200:
                        logout_response = requests.post(f"{BASE_URL}/auth/logout", headers=headers, timeout=10)
                        session_duration = time.time() - start_time
                        
                        if logout_response.status_code == 200:
                            self.log_result("User Journey", "Session Management", True, session_duration,
                                          "Profile accessed and clean logout completed")
                        else:
                            self.log_result("User Journey", "Session Management", False, session_duration,
                                          "Logout failed")
                    else:
                        self.log_result("User Journey", "Session Management", False, 0,
                                      "Profile access failed")
                    
                    return True
                else:
                    self.log_result("User Journey", "Account Setup & Login", False, 0,
                                  "Login failed after registration")
            else:
                self.log_result("User Journey", "Account Setup & Login", False, 0,
                              "User registration failed")
                
        except Exception as e:
            self.log_result("User Journey", "Complete Journey", False, 0, f"Journey error: {e}")
        
        return False

    def test_system_health_check(self):
        """Test overall system health and availability"""
        print(f"\\n🔍 TESTING SYSTEM HEALTH CHECK...")
        
        health_checks = [
            {"name": "API Root", "url": "/", "method": "GET"},
            {"name": "Auth Endpoint", "url": "/auth/login", "method": "POST", 
             "data": {"username": "invalid", "password": "test"}},  # Expected to fail but endpoint should respond
            {"name": "Weather Endpoint", "url": "/weather", "method": "POST", 
             "data": {"latitude": 0, "longitude": 0}},
            {"name": "Port Weather", "url": "/port-weather/singapore", "method": "GET"},
            {"name": "Public Chat", "url": "/public/chat", "method": "POST", 
             "data": {"query": "System health check"}},
        ]
        
        for check in health_checks:
            try:
                start_time = time.time()
                
                if check["method"] == "GET":
                    response = requests.get(f"{BASE_URL}{check['url']}", timeout=10)
                else:
                    response = requests.post(f"{BASE_URL}{check['url']}", 
                                           json=check.get("data", {}), timeout=10)
                
                duration = time.time() - start_time
                
                # For health checks, we care that the endpoint responds, not necessarily success
                if response.status_code < 500:  # Not a server error
                    self.log_result("System Health", f"{check['name']} Availability", True, duration,
                                  f"Endpoint responsive (HTTP {response.status_code})")
                else:
                    self.log_result("System Health", f"{check['name']} Availability", False, duration,
                                  f"Server error: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result("System Health", f"{check['name']} Availability", False, 0, 
                              f"Connection error: {e}")

    def print_integration_summary(self):
        """Print comprehensive integration test results"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        
        # Group results by workflow
        workflow_results = {}
        for result in self.results:
            workflow = result['workflow']
            if workflow not in workflow_results:
                workflow_results[workflow] = {'passed': 0, 'failed': 0, 'tests': []}
            
            if result['passed']:
                workflow_results[workflow]['passed'] += 1
            else:
                workflow_results[workflow]['failed'] += 1
            
            workflow_results[workflow]['tests'].append(result)
        
        print("\\n" + "="*80)
        print("🚢 MARITIME ASSISTANT - END-TO-END INTEGRATION TEST RESULTS")
        print("="*80)
        
        # Overall Integration Rating
        integration_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        if integration_score >= 95:
            integration_rating = "🚀 EXCELLENT"
            color = "🟢"
        elif integration_score >= 85:
            integration_rating = "✅ VERY GOOD"
            color = "🟡"  
        elif integration_score >= 75:
            integration_rating = "⚠️ GOOD"
            color = "🟠"
        else:
            integration_rating = "❌ NEEDS IMPROVEMENT"
            color = "🔴"
        
        print(f"\\n🎯 OVERALL INTEGRATION RATING: {integration_score:.1f}% - {integration_rating}")
        print(f"{color} INTEGRATION STATUS: {integration_rating}")
        
        print(f"\\n📊 SUMMARY:")
        print(f"   ✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"   ❌ Tests Failed: {failed_tests}/{total_tests}")
        print(f"   📈 Success Rate: {integration_score:.1f}%")
        print(f"   ⏱️ Total Test Time: {total_time:.2f}s")
        print(f"   👥 Active Users: {len(self.users)}")
        
        # Workflow Analysis
        print(f"\\n📋 WORKFLOW RESULTS:")
        for workflow, data in workflow_results.items():
            total = data['passed'] + data['failed']
            success_rate = (data['passed'] / total) * 100 if total > 0 else 0
            status = "✅" if success_rate >= 80 else "❌"
            print(f"   {status} {workflow}: {data['passed']}/{total} ({success_rate:.1f}%)")
        
        # Detailed Results
        print(f"\\n📝 DETAILED INTEGRATION RESULTS:")
        for i, result in enumerate(self.results, 1):
            print(f"   {i:2d}. {result['status']} - {result['workflow']}: {result['step']} ({result['duration']:.2f}s)")
            if result['details']:
                print(f"       → {result['details']}")
        
        print(f"\\n🔍 INTEGRATION CATEGORIES TESTED:")
        print("   • User registration and authentication workflows")
        print("   • Weather data retrieval workflows")
        print("   • AI assistant interaction flows")
        print("   • Multi-user concurrent operations")
        print("   • Error handling and recovery")
        print("   • Complete user journey simulation")
        print("   • System health and availability")
        
        # Integration Assessment
        print(f"\\n📈 INTEGRATION ASSESSMENT:")
        if integration_score >= 95:
            print("   🚀 EXCELLENT INTEGRATION - All workflows working perfectly!")
            print("   ✅ System ready for production deployment")
            print("   🎯 Complete end-to-end functionality validated")
        elif integration_score >= 85:
            print("   ✅ VERY GOOD INTEGRATION - System working well")
            print("   💡 Minor workflow optimizations possible")
            print("   🎯 Suitable for production with monitoring")
        elif integration_score >= 75:
            print("   ⚠️ GOOD INTEGRATION - Some workflow issues")
            print("   🔧 Integration improvements recommended")
            print("   📊 Monitor workflows in production")
        else:
            print("   ❌ INTEGRATION NEEDS IMPROVEMENT")
            print("   🔧 Significant workflow fixes required")
            print("   ⚠️ Not recommended for production")
        
        # User Experience Summary
        total_users_created = len([r for r in self.results if "Register" in r['step'] and r['passed']])
        successful_journeys = len([r for r in self.results if "Complete Journey" in r['step'] and r['passed']])
        
        print(f"\\n👥 USER EXPERIENCE SUMMARY:")
        print(f"   📝 Users Created: {total_users_created}")
        print(f"   🚢 Complete Journeys: {successful_journeys}")
        print(f"   🔐 Authentication Success: {len(self.users)} active sessions")
        
        print("="*80)

def main():
    print("🚢 MARITIME ASSISTANT - END-TO-END INTEGRATION TESTING")
    print("=" * 65)
    print("Testing complete system workflows and user journeys...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 65)
    
    suite = IntegrationTestSuite()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly. Please ensure the backend server is running.")
            return
    except Exception:
        print("❌ Cannot connect to server. Please ensure the backend server is running at http://localhost:8000")
        return
    
    print("\\n🚀 Starting comprehensive integration testing...")
    
    # Run all integration workflows
    suite.test_system_health_check()
    suite.test_user_registration_workflow()
    suite.test_weather_data_workflow()
    suite.test_ai_assistant_workflow()
    suite.test_multi_user_workflow()
    suite.test_error_handling_workflow()
    suite.test_complete_user_journey()
    
    # Print comprehensive integration summary
    suite.print_integration_summary()

if __name__ == "__main__":
    main()
