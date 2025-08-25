#!/usr/bin/env python3
"""
🗺️ MARITIME ASSISTANT - ACTUAL ROUTING FUNCTIONALITY TEST
=========================================================

Testing the implemented maritime routing functionality:
- /routes/optimize endpoint
- Route optimization between ports  
- Distance and time calculations
- Fuel consumption estimates
- Professional routing service integration

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import time
import math
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class ActualRoutingTestSuite:
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

    def test_server_connection(self):
        """Test if the server is running"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/docs", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Server Connection", True, response_time, "Server is running")
                return True
            else:
                self.log_result("Server Connection", False, response_time, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Server Connection", False, 0, f"Connection failed: {e}")
            return False

    def test_basic_route_optimization(self):
        """Test basic route optimization between major ports"""
        test_routes = [
            {
                "name": "Singapore to Rotterdam",
                "origin": {"lat": 1.3521, "lng": 103.8198},
                "destination": {"lat": 51.9244, "lng": 4.4777},
                "expected_distance_range": (8500, 12000)  # nautical miles
            },
            {
                "name": "New York to Hamburg",
                "origin": {"lat": 40.7128, "lng": -74.0060},
                "destination": {"lat": 53.5511, "lng": 9.9937},
                "expected_distance_range": (3000, 4500)
            },
            {
                "name": "Shanghai to Los Angeles",
                "origin": {"lat": 31.2304, "lng": 121.4737},
                "destination": {"lat": 34.0522, "lng": -118.2437},
                "expected_distance_range": (5000, 7500)
            }
        ]

        for route in test_routes:
            try:
                start_time = time.time()
                
                payload = {
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "vessel_type": "container",
                    "optimization": "weather"
                }
                
                response = requests.post(f"{BASE_URL}/routes/optimize", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ['distance_nm', 'estimated_time_hours', 'fuel_consumption_mt', 'route_points']
                    missing_fields = [f for f in required_fields if f not in data]
                    
                    if missing_fields:
                        self.log_result(f"Route Optimization: {route['name']}", False, response_time,
                                      f"Missing fields: {missing_fields}")
                    else:
                        distance = data.get('distance_nm', 0)
                        time_hours = data.get('estimated_time_hours', 0)
                        fuel_mt = data.get('fuel_consumption_mt', 0)
                        route_points = data.get('route_points', [])
                        
                        # Validate distance is reasonable
                        min_dist, max_dist = route['expected_distance_range']
                        
                        if min_dist <= distance <= max_dist:
                            self.log_result(f"Route Optimization: {route['name']}", True, response_time,
                                          f"Distance: {distance:.0f} nm, Time: {time_hours:.1f}h, Fuel: {fuel_mt:.0f}t, Points: {len(route_points)}")
                        else:
                            self.log_result(f"Route Optimization: {route['name']}", False, response_time,
                                          f"Distance {distance:.0f} nm outside expected range {min_dist}-{max_dist}")
                else:
                    self.log_result(f"Route Optimization: {route['name']}", False, response_time,
                                  f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                self.log_result(f"Route Optimization: {route['name']}", False, 0, f"Error: {e}")

    def test_vessel_types(self):
        """Test route optimization with different vessel types"""
        vessel_types = ["container", "bulk", "tanker", "cruise", "cargo"]
        
        for vessel_type in vessel_types:
            try:
                start_time = time.time()
                
                payload = {
                    "origin": {"lat": 51.9244, "lng": 4.4777},      # Rotterdam
                    "destination": {"lat": 1.3521, "lng": 103.8198}, # Singapore
                    "vessel_type": vessel_type,
                    "optimization": "fuel"
                }
                
                response = requests.post(f"{BASE_URL}/routes/optimize", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    distance = data.get('distance_nm', 0)
                    fuel = data.get('fuel_consumption_mt', 0)
                    route_type = data.get('route_type', 'unknown')
                    
                    if distance > 0 and fuel > 0:
                        self.log_result(f"Vessel Type: {vessel_type.title()}", True, response_time,
                                      f"Route: {route_type}, Distance: {distance:.0f}nm, Fuel: {fuel:.0f}t")
                    else:
                        self.log_result(f"Vessel Type: {vessel_type.title()}", False, response_time,
                                      "Invalid distance or fuel consumption")
                else:
                    self.log_result(f"Vessel Type: {vessel_type.title()}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Vessel Type: {vessel_type.title()}", False, 0, f"Error: {e}")

    def test_optimization_modes(self):
        """Test different optimization modes"""
        optimization_modes = ["weather", "fuel", "time", "cost"]
        
        for opt_mode in optimization_modes:
            try:
                start_time = time.time()
                
                payload = {
                    "origin": {"lat": 40.7128, "lng": -74.0060},    # New York
                    "destination": {"lat": 51.5074, "lng": -0.1278}, # London
                    "vessel_type": "container",
                    "optimization": opt_mode
                }
                
                response = requests.post(f"{BASE_URL}/routes/optimize", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    distance = data.get('distance_nm', 0)
                    time_hours = data.get('estimated_time_hours', 0)
                    fuel = data.get('fuel_consumption_mt', 0)
                    
                    self.log_result(f"Optimization Mode: {opt_mode.title()}", True, response_time,
                                  f"Distance: {distance:.0f}nm, Time: {time_hours:.1f}h, Fuel: {fuel:.0f}t")
                else:
                    self.log_result(f"Optimization Mode: {opt_mode.title()}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Optimization Mode: {opt_mode.title()}", False, 0, f"Error: {e}")

    def test_response_structure(self):
        """Test response structure completeness"""
        try:
            start_time = time.time()
            
            payload = {
                "origin": {"lat": 1.3521, "lng": 103.8198},
                "destination": {"lat": 22.3193, "lng": 114.1694},
                "vessel_type": "bulk",
                "optimization": "weather"
            }
            
            response = requests.post(f"{BASE_URL}/routes/optimize", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all expected fields
                expected_fields = [
                    'distance_nm', 'estimated_time_hours', 'fuel_consumption_mt',
                    'route_points', 'weather_warnings', 'route_type', 'vessel_type', 'routing_details'
                ]
                
                present_fields = []
                missing_fields = []
                
                for field in expected_fields:
                    if field in data:
                        present_fields.append(field)
                    else:
                        missing_fields.append(field)
                
                if len(missing_fields) == 0:
                    self.log_result("Response Structure", True, response_time,
                                  f"All {len(expected_fields)} fields present")
                else:
                    self.log_result("Response Structure", False, response_time,
                                  f"Missing fields: {missing_fields}")
            else:
                self.log_result("Response Structure", False, response_time,
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Response Structure", False, 0, f"Error: {e}")

    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        
        # Test invalid coordinates
        try:
            start_time = time.time()
            
            payload = {
                "origin": {"lat": 200, "lng": 300},  # Invalid coordinates
                "destination": {"lat": 51.5074, "lng": -0.1278},
                "vessel_type": "container",
                "optimization": "weather"
            }
            
            response = requests.post(f"{BASE_URL}/routes/optimize", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            # Should either reject with 400 or handle gracefully
            if response.status_code == 400:
                self.log_result("Error Handling - Invalid Coordinates", True, response_time,
                              "Correctly rejected invalid coordinates")
            elif response.status_code == 200:
                data = response.json()
                # Check if it's a fallback route
                if 'error' in data.get('routing_details', {}) or data.get('route_type') == 'fallback_direct':
                    self.log_result("Error Handling - Invalid Coordinates", True, response_time,
                                  "Graceful fallback to direct route")
                else:
                    self.log_result("Error Handling - Invalid Coordinates", False, response_time,
                                  "Did not handle invalid coordinates properly")
            else:
                self.log_result("Error Handling - Invalid Coordinates", False, response_time,
                              f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Error Handling - Invalid Coordinates", False, 0, f"Error: {e}")

    def test_performance_benchmarks(self):
        """Test performance with multiple route requests"""
        routes = [
            {"origin": {"lat": 1.3521, "lng": 103.8198}, "destination": {"lat": 22.3193, "lng": 114.1694}},  # Singapore to Hong Kong
            {"origin": {"lat": 51.9244, "lng": 4.4777}, "destination": {"lat": 53.5511, "lng": 9.9937}},   # Rotterdam to Hamburg
            {"origin": {"lat": 40.7128, "lng": -74.0060}, "destination": {"lat": 25.7617, "lng": -80.1918}} # New York to Miami
        ]
        
        total_time = 0
        successful_requests = 0
        
        for i, route in enumerate(routes):
            try:
                start_time = time.time()
                
                payload = {
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "vessel_type": "container",
                    "optimization": "fuel"
                }
                
                response = requests.post(f"{BASE_URL}/routes/optimize", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                total_time += response_time
                
                if response.status_code == 200:
                    successful_requests += 1
                    
            except Exception:
                pass
        
        if successful_requests > 0:
            avg_time = total_time / len(routes)
            if avg_time < 5.0:  # Should be under 5 seconds on average
                self.log_result("Performance Benchmark", True, avg_time,
                              f"Avg response time: {avg_time:.2f}s, Success rate: {successful_requests}/{len(routes)}")
            else:
                self.log_result("Performance Benchmark", False, avg_time,
                              f"Too slow: {avg_time:.2f}s average")
        else:
            self.log_result("Performance Benchmark", False, 0, "No successful requests")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\\n" + "="*80)
        print("🗺️ MARITIME ROUTING FUNCTIONALITY TEST RESULTS")
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
        
        print("\\n🗺️ TESTED FUNCTIONALITY:")
        print("   • Basic route optimization (/routes/optimize)")
        print("   • Multiple vessel types (container, bulk, tanker, cruise, cargo)")
        print("   • Different optimization modes (weather, fuel, time, cost)")
        print("   • Response structure validation")
        print("   • Error handling (invalid coordinates)")
        print("   • Performance benchmarks")
        
        if passed_tests == total_tests:
            print("\\n🎉 RESULT: MARITIME ROUTING FUNCTIONALITY IS PERFECT! 🎉")
        elif passed_tests >= total_tests * 0.8:
            print("\\n✅ RESULT: MARITIME ROUTING FUNCTIONALITY IS MOSTLY WORKING")
        else:
            print("\\n⚠️ RESULT: MARITIME ROUTING NEEDS ATTENTION")
        
        print("="*80)

def main():
    print("🗺️ MARITIME ASSISTANT - ACTUAL ROUTING FUNCTIONALITY TESTING")
    print("=" * 60)
    print("Testing the implemented route optimization functionality...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 60)
    
    suite = ActualRoutingTestSuite()
    
    # Run all tests
    if suite.test_server_connection():
        suite.test_basic_route_optimization()
        suite.test_vessel_types()
        suite.test_optimization_modes()
        suite.test_response_structure()
        suite.test_error_handling()
        suite.test_performance_benchmarks()
    else:
        print("❌ Server not responding. Please ensure the backend server is running.")
        return
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
