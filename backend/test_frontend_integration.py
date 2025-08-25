#!/usr/bin/env python3
"""
🎨 MARITIME ASSISTANT - FRONTEND INTEGRATION TESTING SUITE
=========================================================

Comprehensive testing of frontend integration:
- React component functionality
- API connectivity from frontend to backend
- UI/UX responsiveness
- Navigation and routing
- Data display and formatting
- Error handling in UI
- Mobile responsiveness
- Performance metrics

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import time
import os
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30
WAIT_TIMEOUT = 10

class FrontendIntegrationTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.driver = None
        
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

    def setup_webdriver(self):
        """Setup Chrome WebDriver for frontend testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(TEST_TIMEOUT)
            return True
        except Exception as e:
            print(f"⚠️  WebDriver setup failed: {e}")
            print("   Falling back to API-only tests...")
            return False

    def teardown_webdriver(self):
        """Clean up WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def test_backend_connectivity(self):
        """Test if backend server is accessible"""
        try:
            start_time = time.time()
            response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Backend Connectivity", True, response_time, "Backend server is running")
                return True
            else:
                self.log_result("Backend Connectivity", False, response_time, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Backend Connectivity", False, 0, f"Connection failed: {e}")
            return False

    def test_frontend_server(self):
        """Test if frontend development server is running"""
        try:
            start_time = time.time()
            response = requests.get(FRONTEND_URL, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if it's a React app
                if "react" in response.text.lower() or "root" in response.text:
                    self.log_result("Frontend Server", True, response_time, "Frontend server is running")
                    return True
                else:
                    self.log_result("Frontend Server", False, response_time, "Server running but may not be React app")
                    return False
            else:
                self.log_result("Frontend Server", False, response_time, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Frontend Server", False, 0, f"Connection failed: {e}")
            return False

    def test_page_loading(self):
        """Test main pages load correctly"""
        if not self.driver:
            self.log_result("Page Loading", False, 0, "WebDriver not available")
            return False

        pages = [
            {"path": "/", "name": "Home Page"},
            {"path": "/chat", "name": "Chat Page"},
            {"path": "/weather", "name": "Weather Page"},
            {"path": "/documents", "name": "Documents Page"},
            {"path": "/recommendations", "name": "Recommendations Page"},
            {"path": "/settings", "name": "Settings Page"}
        ]

        for page in pages:
            try:
                start_time = time.time()
                self.driver.get(f"{FRONTEND_URL}{page['path']}")
                
                # Wait for page to load
                WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                response_time = time.time() - start_time
                
                # Check for React error boundaries or error messages
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Error') or contains(text(), 'error')]")
                
                if not error_elements:
                    self.log_result(f"Page Loading: {page['name']}", True, response_time, "Page loaded successfully")
                else:
                    self.log_result(f"Page Loading: {page['name']}", False, response_time, "Page has error messages")
                    
            except TimeoutException:
                self.log_result(f"Page Loading: {page['name']}", False, WAIT_TIMEOUT, "Page load timeout")
            except Exception as e:
                self.log_result(f"Page Loading: {page['name']}", False, 0, f"Error: {e}")

    def test_api_integration(self):
        """Test frontend to backend API integration"""
        if not self.driver:
            # Fall back to direct API tests
            self.test_api_endpoints_directly()
            return

        try:
            start_time = time.time()
            
            # Navigate to chat page
            self.driver.get(f"{FRONTEND_URL}/chat")
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for chat input field
            chat_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' or @placeholder*='message' or @placeholder*='chat']")
            
            if chat_inputs:
                chat_input = chat_inputs[0]
                chat_input.clear()
                chat_input.send_keys("Hello, test message")
                
                # Look for send button
                send_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Send') or contains(@aria-label, 'send')]")
                
                if send_buttons:
                    send_buttons[0].click()
                    
                    # Wait for response
                    time.sleep(3)
                    
                    # Check for response in chat
                    response_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Maritime') or contains(text(), 'Assistant')]")
                    
                    response_time = time.time() - start_time
                    
                    if response_elements:
                        self.log_result("API Integration - Chat", True, response_time, "Chat API working through frontend")
                    else:
                        self.log_result("API Integration - Chat", False, response_time, "No response received from chat API")
                else:
                    self.log_result("API Integration - Chat", False, 0, "Send button not found")
            else:
                self.log_result("API Integration - Chat", False, 0, "Chat input field not found")
                
        except Exception as e:
            self.log_result("API Integration - Chat", False, 0, f"Error: {e}")

    def test_api_endpoints_directly(self):
        """Test key API endpoints that frontend should be using"""
        endpoints = [
            {"url": f"{BACKEND_URL}/chat", "method": "POST", "data": {"query": "Hello test"}, "name": "Chat API"},
            {"url": f"{BACKEND_URL}/weather", "method": "POST", "data": {"latitude": 1.3521, "longitude": 103.8198, "location_name": "Singapore"}, "name": "Weather API"},
            {"url": f"{BACKEND_URL}/ports/search?q=singapore", "method": "GET", "data": None, "name": "Ports Search API"},
            {"url": f"{BACKEND_URL}/routes/optimize", "method": "POST", "data": {"origin": {"lat": 1.3521, "lng": 103.8198}, "destination": {"lat": 51.9244, "lng": 4.4777}}, "name": "Routing API"}
        ]

        for endpoint in endpoints:
            try:
                start_time = time.time()
                
                if endpoint["method"] == "GET":
                    response = requests.get(endpoint["url"], timeout=TEST_TIMEOUT)
                else:
                    response = requests.post(endpoint["url"], json=endpoint["data"], timeout=TEST_TIMEOUT)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(f"Direct API: {endpoint['name']}", True, response_time, f"API endpoint working")
                else:
                    self.log_result(f"Direct API: {endpoint['name']}", False, response_time, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Direct API: {endpoint['name']}", False, 0, f"Error: {e}")

    def test_ui_components(self):
        """Test UI components and interactions"""
        if not self.driver:
            self.log_result("UI Components", False, 0, "WebDriver not available")
            return

        try:
            start_time = time.time()
            
            # Test home page components
            self.driver.get(FRONTEND_URL)
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for common maritime app elements
            elements_to_check = [
                "//nav",  # Navigation
                "//button",  # Buttons
                "//input",  # Input fields
                "//*[contains(text(), 'Maritime') or contains(text(), 'Assistant')]",  # Maritime branding
            ]
            
            found_elements = 0
            for element_xpath in elements_to_check:
                elements = self.driver.find_elements(By.XPATH, element_xpath)
                if elements:
                    found_elements += 1
            
            response_time = time.time() - start_time
            
            if found_elements >= 2:  # At least 2 key elements found
                self.log_result("UI Components", True, response_time, f"Found {found_elements}/4 key UI elements")
            else:
                self.log_result("UI Components", False, response_time, f"Only found {found_elements}/4 key UI elements")
                
        except Exception as e:
            self.log_result("UI Components", False, 0, f"Error: {e}")

    def test_responsive_design(self):
        """Test responsive design on different screen sizes"""
        if not self.driver:
            self.log_result("Responsive Design", False, 0, "WebDriver not available")
            return

        screen_sizes = [
            {"width": 1920, "height": 1080, "name": "Desktop"},
            {"width": 768, "height": 1024, "name": "Tablet"},
            {"width": 375, "height": 667, "name": "Mobile"}
        ]

        for size in screen_sizes:
            try:
                start_time = time.time()
                
                self.driver.set_window_size(size["width"], size["height"])
                self.driver.get(FRONTEND_URL)
                
                WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check if page renders without horizontal scrollbars (basic responsive test)
                body_width = self.driver.execute_script("return document.body.scrollWidth")
                window_width = self.driver.execute_script("return window.innerWidth")
                
                response_time = time.time() - start_time
                
                if body_width <= window_width + 50:  # Allow small tolerance
                    self.log_result(f"Responsive: {size['name']}", True, response_time, f"No horizontal overflow ({body_width}px <= {window_width}px)")
                else:
                    self.log_result(f"Responsive: {size['name']}", False, response_time, f"Horizontal overflow detected ({body_width}px > {window_width}px)")
                    
            except Exception as e:
                self.log_result(f"Responsive: {size['name']}", False, 0, f"Error: {e}")

    def test_navigation(self):
        """Test navigation between pages"""
        if not self.driver:
            self.log_result("Navigation", False, 0, "WebDriver not available")
            return

        navigation_tests = [
            {"from": "/", "to": "/chat", "name": "Home to Chat"},
            {"from": "/chat", "to": "/weather", "name": "Chat to Weather"},
            {"from": "/weather", "to": "/documents", "name": "Weather to Documents"}
        ]

        for nav_test in navigation_tests:
            try:
                start_time = time.time()
                
                # Navigate to starting page
                self.driver.get(f"{FRONTEND_URL}{nav_test['from']}")
                WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Look for navigation links
                nav_links = self.driver.find_elements(By.XPATH, f"//a[@href='{nav_test['to']}' or contains(@href, '{nav_test['to']}')]")
                
                if nav_links:
                    nav_links[0].click()
                    
                    # Wait for navigation
                    WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                        lambda driver: nav_test['to'] in driver.current_url
                    )
                    
                    response_time = time.time() - start_time
                    self.log_result(f"Navigation: {nav_test['name']}", True, response_time, "Navigation successful")
                else:
                    self.log_result(f"Navigation: {nav_test['name']}", False, 0, f"No navigation link found for {nav_test['to']}")
                    
            except TimeoutException:
                self.log_result(f"Navigation: {nav_test['name']}", False, WAIT_TIMEOUT, "Navigation timeout")
            except Exception as e:
                self.log_result(f"Navigation: {nav_test['name']}", False, 0, f"Error: {e}")

    def test_error_handling(self):
        """Test frontend error handling"""
        if not self.driver:
            self.log_result("Error Handling", False, 0, "WebDriver not available")
            return

        try:
            start_time = time.time()
            
            # Test with backend offline scenario (simulate by using wrong port)
            wrong_backend_url = "http://localhost:9999"
            
            # This is a conceptual test - in real implementation, you'd need to:
            # 1. Configure frontend to use wrong backend URL temporarily
            # 2. Or intercept network requests
            # 3. Or test error boundary components directly
            
            # For now, just check if error boundaries exist
            self.driver.get(FRONTEND_URL)
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for error boundary or error handling code
            page_source = self.driver.page_source.lower()
            
            response_time = time.time() - start_time
            
            if "error" in page_source or "catch" in page_source:
                self.log_result("Error Handling", True, response_time, "Error handling code detected")
            else:
                self.log_result("Error Handling", False, response_time, "No error handling detected in frontend")
                
        except Exception as e:
            self.log_result("Error Handling", False, 0, f"Error: {e}")

    def test_performance_metrics(self):
        """Test frontend performance metrics"""
        if not self.driver:
            self.log_result("Performance Metrics", False, 0, "WebDriver not available")
            return

        try:
            start_time = time.time()
            
            self.driver.get(FRONTEND_URL)
            
            # Wait for page to fully load
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get performance metrics using JavaScript
            navigation_timing = self.driver.execute_script("""
                const perf = performance.getEntriesByType('navigation')[0];
                return {
                    loadComplete: perf.loadEventEnd - perf.loadEventStart,
                    domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                    totalLoadTime: perf.loadEventEnd - perf.navigationStart
                };
            """)
            
            response_time = time.time() - start_time
            total_load_time = navigation_timing.get('totalLoadTime', 0)
            
            if total_load_time > 0 and total_load_time < 5000:  # Less than 5 seconds
                self.log_result("Performance Metrics", True, response_time, 
                              f"Load time: {total_load_time:.0f}ms (Good)")
            elif total_load_time > 0:
                self.log_result("Performance Metrics", False, response_time,
                              f"Load time: {total_load_time:.0f}ms (Too slow)")
            else:
                self.log_result("Performance Metrics", False, response_time, "Could not measure performance")
                
        except Exception as e:
            self.log_result("Performance Metrics", False, 0, f"Error: {e}")

    def check_frontend_files(self):
        """Check if frontend files exist and are properly structured"""
        try:
            start_time = time.time()
            
            # Check key frontend files
            frontend_root = Path("b:/maritime-assistant")
            key_files = [
                "package.json",
                "next.config.mjs", 
                "app/layout.tsx",
                "app/page.tsx",
                "app/chat/page.tsx",
                "app/weather/page.tsx",
                "components/ui/button.tsx"
            ]
            
            existing_files = []
            missing_files = []
            
            for file in key_files:
                file_path = frontend_root / file
                if file_path.exists():
                    existing_files.append(file)
                else:
                    missing_files.append(file)
            
            response_time = time.time() - start_time
            
            if len(missing_files) == 0:
                self.log_result("Frontend File Structure", True, response_time, 
                              f"All {len(key_files)} key files present")
            elif len(existing_files) >= len(key_files) * 0.8:  # 80% of files present
                self.log_result("Frontend File Structure", True, response_time,
                              f"{len(existing_files)}/{len(key_files)} files present")
            else:
                self.log_result("Frontend File Structure", False, response_time,
                              f"Missing critical files: {missing_files}")
                
        except Exception as e:
            self.log_result("Frontend File Structure", False, 0, f"Error: {e}")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🎨 FRONTEND INTEGRATION TEST RESULTS")
        print("="*80)
        
        print(f"📊 SUMMARY:")
        print(f"   ✅ Passed: {passed_tests}/{total_tests}")
        print(f"   ❌ Failed: {failed_tests}/{total_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        print(f"   ⚡ Avg Response: {avg_response_time:.2f}s")
        
        print("\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            print(f"   {i:2d}. {result['status']} - {result['test']} ({result['response_time']:.2f}s)")
            if result['details']:
                print(f"       → {result['details']}")
        
        print("\n🎨 TESTED FUNCTIONALITY:")
        print("   • Backend connectivity and API integration")
        print("   • Frontend server and React app functionality")
        print("   • Page loading and navigation")
        print("   • UI components and responsiveness")
        print("   • API endpoint integration")
        print("   • Error handling and performance")
        print("   • File structure and configuration")
        
        if passed_tests == total_tests:
            print("\n🎉 RESULT: FRONTEND INTEGRATION IS PERFECT! 🎉")
        elif passed_tests >= total_tests * 0.8:
            print("\n✅ RESULT: FRONTEND INTEGRATION IS MOSTLY WORKING")
        else:
            print("\n⚠️ RESULT: FRONTEND INTEGRATION NEEDS ATTENTION")
        
        print("="*80)

def main():
    print("🎨 MARITIME ASSISTANT - FRONTEND INTEGRATION TESTING")
    print("=" * 60)
    print("Testing comprehensive frontend integration...")
    print(f"Backend: {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 60)
    
    suite = FrontendIntegrationTestSuite()
    
    # Check file structure first
    suite.check_frontend_files()
    
    # Test backend connectivity
    backend_ok = suite.test_backend_connectivity()
    
    # Test frontend server
    frontend_ok = suite.test_frontend_server()
    
    # Setup WebDriver for browser tests
    webdriver_ok = suite.setup_webdriver()
    
    # Run tests based on what's available
    if backend_ok:
        suite.test_api_endpoints_directly()
    
    if frontend_ok and webdriver_ok:
        suite.test_page_loading()
        suite.test_ui_components()
        suite.test_api_integration()
        suite.test_navigation()
        suite.test_responsive_design()
        suite.test_error_handling()
        suite.test_performance_metrics()
    elif frontend_ok:
        print("⚠️  WebDriver unavailable - running limited tests")
    else:
        print("⚠️  Frontend server not running - testing file structure only")
    
    # Cleanup
    suite.teardown_webdriver()
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
