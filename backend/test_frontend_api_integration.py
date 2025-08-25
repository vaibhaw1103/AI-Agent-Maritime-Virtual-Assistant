#!/usr/bin/env python3
"""
🎨 MARITIME ASSISTANT - FRONTEND INTEGRATION TESTING SUITE
=========================================================

Comprehensive testing of frontend integration:
- Frontend file structure validation
- API connectivity from backend perspective  
- Next.js configuration analysis
- Component structure verification
- Package dependencies check
- Build system validation

Version: 1.0 (API-focused)
Date: August 22, 2025
"""

import requests
import json
import time
import os
import subprocess
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30

class FrontendIntegrationTestSuite:
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
                # Check if it's a React/Next.js app
                content = response.text.lower()
                if any(keyword in content for keyword in ["next", "react", "__next", "_next"]):
                    self.log_result("Frontend Server", True, response_time, "Next.js/React app detected")
                    return True
                else:
                    self.log_result("Frontend Server", True, response_time, "Frontend server running (type unknown)")
                    return True
            else:
                self.log_result("Frontend Server", False, response_time, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Frontend Server", False, 0, f"Connection failed: {e}")
            return False

    def test_api_endpoints_for_frontend(self):
        """Test key API endpoints that frontend should be using"""
        endpoints = [
            {
                "url": f"{BACKEND_URL}/chat",
                "method": "POST", 
                "data": {"query": "Hello from frontend test"},
                "name": "Chat API",
                "expected_fields": ["response", "confidence", "conversation_id"]
            },
            {
                "url": f"{BACKEND_URL}/weather",
                "method": "POST",
                "data": {"latitude": 1.3521, "longitude": 103.8198, "location_name": "Singapore"},
                "name": "Weather API",
                "expected_fields": ["current_weather", "forecast", "marine_conditions"]
            },
            {
                "url": f"{BACKEND_URL}/api/ports/search?query=singapore",
                "method": "GET",
                "data": None,
                "name": "Ports Search API",
                "expected_fields": None  # Expect array
            },
            {
                "url": f"{BACKEND_URL}/routes/optimize",
                "method": "POST",
                "data": {
                    "origin": {"lat": 1.3521, "lng": 103.8198},
                    "destination": {"lat": 51.9244, "lng": 4.4777},
                    "vessel_type": "container"
                },
                "name": "Routing API",
                "expected_fields": ["distance_nm", "estimated_time_hours", "route_points"]
            }
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
                    data = response.json()
                    
                    # Validate response structure for frontend consumption
                    if endpoint["expected_fields"]:
                        missing_fields = [f for f in endpoint["expected_fields"] if f not in data]
                        if missing_fields:
                            self.log_result(f"Frontend API: {endpoint['name']}", False, response_time,
                                          f"Missing fields for frontend: {missing_fields}")
                        else:
                            self.log_result(f"Frontend API: {endpoint['name']}", True, response_time,
                                          f"All required fields present")
                    else:
                        # For array responses
                        if isinstance(data, list):
                            self.log_result(f"Frontend API: {endpoint['name']}", True, response_time,
                                          f"Array response with {len(data)} items")
                        else:
                            self.log_result(f"Frontend API: {endpoint['name']}", True, response_time,
                                          "Valid response structure")
                else:
                    self.log_result(f"Frontend API: {endpoint['name']}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Frontend API: {endpoint['name']}", False, 0, f"Error: {e}")

    def test_cors_configuration(self):
        """Test CORS configuration for frontend-backend communication"""
        try:
            start_time = time.time()
            
            # Test CORS preflight request
            headers = {
                'Origin': FRONTEND_URL,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(f"{BACKEND_URL}/chat", headers=headers, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 204]:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                if any(cors_headers.values()):
                    self.log_result("CORS Configuration", True, response_time,
                                  f"CORS headers present: {list(cors_headers.keys())}")
                else:
                    self.log_result("CORS Configuration", False, response_time,
                                  "No CORS headers found")
            else:
                self.log_result("CORS Configuration", False, response_time,
                              f"CORS preflight failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("CORS Configuration", False, 0, f"Error: {e}")

    def check_frontend_file_structure(self):
        """Check if frontend files exist and are properly structured"""
        try:
            start_time = time.time()
            
            # Check key frontend files
            frontend_root = Path("b:/maritime-assistant")
            
            # Next.js structure
            nextjs_files = [
                "package.json",
                "next.config.mjs",
                "tsconfig.json",
                "app/layout.tsx",
                "app/page.tsx"
            ]
            
            # Pages structure
            page_files = [
                "app/chat/page.tsx",
                "app/weather/page.tsx", 
                "app/documents/page.tsx",
                "app/recommendations/page.tsx",
                "app/settings/page.tsx"
            ]
            
            # Components structure
            component_files = [
                "components/ui/button.tsx",
                "components/ui/input.tsx",
                "components/ui/card.tsx",
                "components/theme-provider.tsx"
            ]
            
            # Check each category
            categories = [
                {"name": "Next.js Core", "files": nextjs_files},
                {"name": "Application Pages", "files": page_files},
                {"name": "UI Components", "files": component_files}
            ]
            
            total_score = 0
            max_score = 0
            
            for category in categories:
                existing = []
                missing = []
                
                for file in category["files"]:
                    file_path = frontend_root / file
                    if file_path.exists():
                        existing.append(file)
                    else:
                        missing.append(file)
                
                score = len(existing) / len(category["files"]) * 100
                total_score += len(existing)
                max_score += len(category["files"])
                
                if score >= 80:
                    self.log_result(f"File Structure: {category['name']}", True, 0,
                                  f"{len(existing)}/{len(category['files'])} files ({score:.0f}%)")
                else:
                    self.log_result(f"File Structure: {category['name']}", False, 0,
                                  f"Missing: {missing[:3]}{'...' if len(missing) > 3 else ''}")
            
            response_time = time.time() - start_time
            
            # Overall assessment
            overall_score = total_score / max_score * 100
            if overall_score >= 70:
                self.log_result("Overall File Structure", True, response_time,
                              f"Frontend structure {overall_score:.0f}% complete")
            else:
                self.log_result("Overall File Structure", False, response_time,
                              f"Frontend structure only {overall_score:.0f}% complete")
                
        except Exception as e:
            self.log_result("Frontend File Structure", False, 0, f"Error: {e}")

    def check_package_dependencies(self):
        """Check package.json for required dependencies"""
        try:
            start_time = time.time()
            
            package_json_path = Path("b:/maritime-assistant/package.json")
            
            if not package_json_path.exists():
                self.log_result("Package Dependencies", False, 0, "package.json not found")
                return
            
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Required dependencies for maritime app
            required_deps = [
                "next",
                "react", 
                "react-dom",
                "@types/react",
                "typescript",
                "tailwindcss"
            ]
            
            dependencies = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
            
            missing_deps = [dep for dep in required_deps if dep not in dependencies]
            present_deps = [dep for dep in required_deps if dep in dependencies]
            
            response_time = time.time() - start_time
            
            if len(missing_deps) == 0:
                self.log_result("Package Dependencies", True, response_time,
                              f"All {len(required_deps)} required dependencies present")
            elif len(present_deps) >= len(required_deps) * 0.8:
                self.log_result("Package Dependencies", True, response_time,
                              f"{len(present_deps)}/{len(required_deps)} dependencies present")
            else:
                self.log_result("Package Dependencies", False, response_time,
                              f"Missing critical dependencies: {missing_deps}")
                
        except Exception as e:
            self.log_result("Package Dependencies", False, 0, f"Error: {e}")

    def check_build_configuration(self):
        """Check Next.js and build configuration"""
        try:
            start_time = time.time()
            
            # Check Next.js config
            config_files = [
                ("next.config.mjs", "Next.js Configuration"),
                ("tsconfig.json", "TypeScript Configuration"), 
                ("tailwind.config.js", "Tailwind CSS Configuration"),
                ("components.json", "shadcn/ui Configuration")
            ]
            
            config_status = []
            
            for config_file, description in config_files:
                config_path = Path(f"b:/maritime-assistant/{config_file}")
                if config_path.exists():
                    config_status.append(f"✅ {description}")
                else:
                    config_status.append(f"❌ {description}")
            
            response_time = time.time() - start_time
            
            present_configs = sum(1 for status in config_status if "✅" in status)
            total_configs = len(config_status)
            
            if present_configs >= total_configs * 0.75:  # 75% of configs present
                self.log_result("Build Configuration", True, response_time,
                              f"{present_configs}/{total_configs} configuration files present")
            else:
                self.log_result("Build Configuration", False, response_time,
                              f"Missing configuration files: {present_configs}/{total_configs}")
                
        except Exception as e:
            self.log_result("Build Configuration", False, 0, f"Error: {e}")

    def test_api_response_format(self):
        """Test API responses are frontend-friendly"""
        try:
            start_time = time.time()
            
            # Test chat API response format
            response = requests.post(f"{BACKEND_URL}/chat", 
                                   json={"query": "Test frontend formatting"},
                                   timeout=TEST_TIMEOUT)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for frontend-friendly formatting
                checks = []
                
                # Check timestamp format
                if "timestamp" in data:
                    try:
                        # Try parsing ISO format timestamp
                        from datetime import datetime
                        datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                        checks.append("✅ Timestamp in ISO format")
                    except:
                        checks.append("❌ Timestamp format not ISO")
                else:
                    checks.append("❌ No timestamp field")
                
                # Check response is string (not object)
                if isinstance(data.get("response"), str):
                    checks.append("✅ Response is string")
                else:
                    checks.append("❌ Response is not string")
                
                # Check confidence is number
                if isinstance(data.get("confidence"), (int, float)):
                    checks.append("✅ Confidence is numeric")
                else:
                    checks.append("❌ Confidence is not numeric")
                
                passed_checks = sum(1 for check in checks if "✅" in check)
                
                if passed_checks >= len(checks) * 0.8:
                    self.log_result("API Response Format", True, response_time,
                                  f"Frontend-friendly format: {passed_checks}/{len(checks)} checks")
                else:
                    self.log_result("API Response Format", False, response_time,
                                  f"Format issues: {[c for c in checks if '❌' in c]}")
            else:
                self.log_result("API Response Format", False, response_time,
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("API Response Format", False, 0, f"Error: {e}")

    def test_static_assets(self):
        """Test static assets and public files"""
        try:
            start_time = time.time()
            
            # Check public directory assets
            public_dir = Path("b:/maritime-assistant/public")
            
            if not public_dir.exists():
                self.log_result("Static Assets", False, 0, "Public directory not found")
                return
            
            # Look for common assets
            asset_types = {
                "images": [".png", ".jpg", ".jpeg", ".svg", ".gif"],
                "icons": [".ico", ".png"], 
                "fonts": [".woff", ".woff2", ".ttf"],
                "data": [".json", ".csv"]
            }
            
            found_assets = {}
            
            for asset_type, extensions in asset_types.items():
                count = 0
                for ext in extensions:
                    count += len(list(public_dir.glob(f"*{ext}")))
                found_assets[asset_type] = count
            
            response_time = time.time() - start_time
            
            total_assets = sum(found_assets.values())
            
            if total_assets > 0:
                self.log_result("Static Assets", True, response_time,
                              f"Found {total_assets} assets: {found_assets}")
            else:
                self.log_result("Static Assets", False, response_time,
                              "No static assets found in public directory")
                
        except Exception as e:
            self.log_result("Static Assets", False, 0, f"Error: {e}")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\\n" + "="*80)
        print("🎨 FRONTEND INTEGRATION TEST RESULTS")
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
        
        print("\\n🎨 TESTED FUNCTIONALITY:")
        print("   • Frontend file structure and configuration")
        print("   • Backend API connectivity for frontend")
        print("   • CORS configuration for cross-origin requests")
        print("   • Package dependencies and build setup")  
        print("   • API response format for frontend consumption")
        print("   • Static assets and public files")
        print("   • Next.js and TypeScript configuration")
        
        if passed_tests == total_tests:
            print("\\n🎉 RESULT: FRONTEND INTEGRATION IS PERFECT! 🎉")
        elif passed_tests >= total_tests * 0.8:
            print("\\n✅ RESULT: FRONTEND INTEGRATION IS MOSTLY WORKING")
        elif passed_tests >= total_tests * 0.6:
            print("\\n⚠️ RESULT: FRONTEND INTEGRATION NEEDS SOME WORK")
        else:
            print("\\n❌ RESULT: FRONTEND INTEGRATION NEEDS SIGNIFICANT ATTENTION")
        
        print("="*80)

def main():
    print("🎨 MARITIME ASSISTANT - FRONTEND INTEGRATION TESTING")
    print("=" * 60)
    print("Testing frontend integration and API connectivity...")
    print(f"Backend: {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 60)
    
    suite = FrontendIntegrationTestSuite()
    
    # Run comprehensive tests
    suite.check_frontend_file_structure()
    suite.check_package_dependencies()
    suite.check_build_configuration()
    suite.test_static_assets()
    
    # Test backend connectivity and APIs
    if suite.test_backend_connectivity():
        suite.test_api_endpoints_for_frontend()
        suite.test_cors_configuration()
        suite.test_api_response_format()
    else:
        print("⚠️  Backend not available - skipping API integration tests")
    
    # Test frontend server if available
    if suite.test_frontend_server():
        print("✅ Frontend server detected - integration testing complete")
    else:
        print("⚠️  Frontend server not running - tested static structure only")
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
