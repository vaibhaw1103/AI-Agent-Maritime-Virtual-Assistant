#!/usr/bin/env python3
"""
🗺️ MARITIME ASSISTANT - MARITIME ROUTING TESTING SUITE
=====================================================

Comprehensive testing of maritime routing functionality:
- Route planning between ports
- Land avoidance algorithms
- Distance calculations
- Weather routing integration
- Great circle vs rhumb line routing
- Multi-waypoint routing
- Route optimization
- Navigation safety

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import time
import math
from datetime import datetime
from typing import List, Dict, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class MaritimeRoutingTestSuite:
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

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance between two points (in nautical miles)"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Earth's radius in nautical miles
        earth_radius_nm = 3440.065
        distance = earth_radius_nm * c
        
        return distance

    def test_server_connection(self):
        """Test if the server is running and accessible"""
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

    def test_basic_route_planning(self):
        """Test basic route planning between major ports"""
        test_routes = [
            {
                "name": "Singapore to Rotterdam",
                "start": {"lat": 1.3521, "lon": 103.8198},
                "end": {"lat": 51.9244, "lon": 4.4777},
                "expected_distance_range": (8500, 11000)  # nautical miles
            },
            {
                "name": "New York to Hamburg", 
                "start": {"lat": 40.7128, "lon": -74.0060},
                "end": {"lat": 53.5511, "lon": 9.9937},
                "expected_distance_range": (3200, 4000)
            },
            {
                "name": "Shanghai to Los Angeles",
                "start": {"lat": 31.2304, "lon": 121.4737},
                "end": {"lat": 34.0522, "lon": -118.2437},
                "expected_distance_range": (5500, 7000)
            }
        ]

        for route in test_routes:
            try:
                start_time = time.time()
                
                payload = {
                    "start_port": route["start"],
                    "end_port": route["end"],
                    "route_type": "shortest",
                    "vessel_type": "container"
                }
                
                response = requests.post(f"{BASE_URL}/routing/plan", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ['route_points', 'total_distance', 'estimated_time']
                    missing_fields = [f for f in required_fields if f not in data]
                    
                    if missing_fields:
                        self.log_result(f"Route Planning: {route['name']}", False, response_time,
                                      f"Missing fields: {missing_fields}")
                    else:
                        # Validate distance is reasonable
                        distance = data.get('total_distance', 0)
                        min_dist, max_dist = route['expected_distance_range']
                        
                        if min_dist <= distance <= max_dist:
                            self.log_result(f"Route Planning: {route['name']}", True, response_time,
                                          f"Distance: {distance:.0f} nm")
                        else:
                            self.log_result(f"Route Planning: {route['name']}", False, response_time,
                                          f"Distance {distance:.0f} nm outside expected range {min_dist}-{max_dist}")
                else:
                    self.log_result(f"Route Planning: {route['name']}", False, response_time,
                                  f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                self.log_result(f"Route Planning: {route['name']}", False, 0, f"Error: {e}")

    def test_land_avoidance(self):
        """Test land avoidance in routing algorithms"""
        test_cases = [
            {
                "name": "Mediterranean Route (Spain to Turkey)",
                "start": {"lat": 36.7201, "lon": -4.4203},  # Malaga, Spain
                "end": {"lat": 41.0082, "lon": 28.9784},    # Istanbul, Turkey
                "should_avoid": ["land", "shallow_water"]
            },
            {
                "name": "Baltic Sea Route (Stockholm to Helsinki)", 
                "start": {"lat": 59.3293, "lon": 18.0686},  # Stockholm
                "end": {"lat": 60.1699, "lon": 24.9384},    # Helsinki
                "should_avoid": ["archipelago", "restricted_areas"]
            }
        ]

        for case in test_cases:
            try:
                start_time = time.time()
                
                payload = {
                    "start_port": case["start"],
                    "end_port": case["end"],
                    "route_type": "safe",
                    "avoid_land": True,
                    "minimum_depth": 20  # meters
                }
                
                response = requests.post(f"{BASE_URL}/routing/plan", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if route points avoid land
                    route_points = data.get('route_points', [])
                    if len(route_points) > 2:  # Should have waypoints to avoid land
                        self.log_result(f"Land Avoidance: {case['name']}", True, response_time,
                                      f"Route has {len(route_points)} waypoints")
                    else:
                        self.log_result(f"Land Avoidance: {case['name']}", False, response_time,
                                      "Route too simple, may not avoid land properly")
                else:
                    self.log_result(f"Land Avoidance: {case['name']}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Land Avoidance: {case['name']}", False, 0, f"Error: {e}")

    def test_weather_routing(self):
        """Test weather-optimized routing"""
        try:
            start_time = time.time()
            
            payload = {
                "start_port": {"lat": 51.9244, "lon": 4.4777},    # Rotterdam
                "end_port": {"lat": 40.7128, "lon": -74.0060},    # New York
                "route_type": "weather_optimized",
                "departure_time": "2025-08-25T08:00:00Z",
                "vessel_type": "bulk_carrier",
                "weather_routing": True
            }
            
            response = requests.post(f"{BASE_URL}/routing/weather-route", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['route_points', 'weather_conditions', 'estimated_fuel_savings']
                if all(field in data for field in required_fields):
                    weather_info = data.get('weather_conditions', {})
                    fuel_savings = data.get('estimated_fuel_savings', 0)
                    
                    self.log_result("Weather Routing", True, response_time,
                                  f"Fuel savings: {fuel_savings}%, Weather waypoints: {len(weather_info)}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Weather Routing", False, response_time,
                                  f"Missing fields: {missing}")
            else:
                self.log_result("Weather Routing", False, response_time,
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Weather Routing", False, 0, f"Error: {e}")

    def test_multi_waypoint_routing(self):
        """Test routing through multiple waypoints"""
        try:
            start_time = time.time()
            
            payload = {
                "waypoints": [
                    {"lat": 1.3521, "lon": 103.8198, "name": "Singapore"},
                    {"lat": 22.3193, "lon": 114.1694, "name": "Hong Kong"}, 
                    {"lat": 31.2304, "lon": 121.4737, "name": "Shanghai"},
                    {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo"}
                ],
                "route_type": "multi_port",
                "optimize_order": True
            }
            
            response = requests.post(f"{BASE_URL}/routing/multi-waypoint", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if 'optimized_route' in data and 'total_distance' in data:
                    optimized_route = data['optimized_route']
                    total_distance = data['total_distance']
                    
                    if len(optimized_route) == 4:  # Should visit all 4 ports
                        self.log_result("Multi-Waypoint Routing", True, response_time,
                                      f"Optimized {len(optimized_route)} waypoints, {total_distance:.0f} nm")
                    else:
                        self.log_result("Multi-Waypoint Routing", False, response_time,
                                      f"Route optimization incomplete: {len(optimized_route)} waypoints")
                else:
                    self.log_result("Multi-Waypoint Routing", False, response_time,
                                  "Missing route optimization data")
            else:
                self.log_result("Multi-Waypoint Routing", False, response_time,
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Multi-Waypoint Routing", False, 0, f"Error: {e}")

    def test_route_types(self):
        """Test different route calculation methods"""
        route_types = [
            ("shortest", "Great Circle Route"),
            ("fastest", "Current-Optimized Route"),
            ("economical", "Fuel-Efficient Route"),
            ("safe", "Weather-Safe Route")
        ]

        for route_type, description in route_types:
            try:
                start_time = time.time()
                
                payload = {
                    "start_port": {"lat": 51.9244, "lon": 4.4777},  # Rotterdam
                    "end_port": {"lat": 1.3521, "lon": 103.8198},   # Singapore
                    "route_type": route_type,
                    "vessel_type": "container"
                }
                
                response = requests.post(f"{BASE_URL}/routing/plan",
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'total_distance' in data and 'estimated_time' in data:
                        distance = data['total_distance']
                        est_time = data['estimated_time']
                        
                        self.log_result(f"Route Type: {description}", True, response_time,
                                      f"Distance: {distance:.0f} nm, Time: {est_time}")
                    else:
                        self.log_result(f"Route Type: {description}", False, response_time,
                                      "Missing distance/time data")
                else:
                    self.log_result(f"Route Type: {description}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Route Type: {description}", False, 0, f"Error: {e}")

    def test_navigation_safety(self):
        """Test navigation safety features"""
        safety_tests = [
            {
                "name": "Shallow Water Avoidance",
                "payload": {
                    "start_port": {"lat": 51.9244, "lon": 4.4777},
                    "end_port": {"lat": 53.5511, "lon": 9.9937},
                    "minimum_depth": 15,
                    "avoid_shallow_water": True
                }
            },
            {
                "name": "Traffic Separation Scheme",
                "payload": {
                    "start_port": {"lat": 50.1109, "lon": 1.8391},   # Dover
                    "end_port": {"lat": 51.0543, "lon": 3.7174},     # Calais
                    "follow_tss": True,
                    "route_type": "safe"
                }
            }
        ]

        for test in safety_tests:
            try:
                start_time = time.time()
                
                response = requests.post(f"{BASE_URL}/routing/safe-route",
                                       json=test["payload"], timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    safety_features = data.get('safety_features', [])
                    if safety_features:
                        self.log_result(f"Navigation Safety: {test['name']}", True, response_time,
                                      f"Safety features: {len(safety_features)}")
                    else:
                        self.log_result(f"Navigation Safety: {test['name']}", False, response_time,
                                      "No safety features implemented")
                else:
                    self.log_result(f"Navigation Safety: {test['name']}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Navigation Safety: {test['name']}", False, 0, f"Error: {e}")

    def test_distance_calculations(self):
        """Test accuracy of distance calculations"""
        known_distances = [
            {
                "route": "New York to London",
                "start": {"lat": 40.7128, "lon": -74.0060},
                "end": {"lat": 51.5074, "lon": -0.1278},
                "expected_distance": 3458,  # nautical miles
                "tolerance": 50
            },
            {
                "route": "Singapore to Tokyo", 
                "start": {"lat": 1.3521, "lon": 103.8198},
                "end": {"lat": 35.6762, "lon": 139.6503},
                "expected_distance": 2865,  # nautical miles
                "tolerance": 50
            }
        ]

        for test in known_distances:
            # Calculate theoretical distance
            calculated_distance = self.calculate_distance(
                test["start"]["lat"], test["start"]["lon"],
                test["end"]["lat"], test["end"]["lon"]
            )
            
            # Test API distance calculation
            try:
                start_time = time.time()
                
                payload = {
                    "start_port": test["start"],
                    "end_port": test["end"],
                    "route_type": "shortest"
                }
                
                response = requests.post(f"{BASE_URL}/routing/distance",
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    api_distance = data.get('distance', 0)
                    
                    # Check if within tolerance
                    expected = test["expected_distance"]
                    tolerance = test["tolerance"]
                    
                    if abs(api_distance - expected) <= tolerance:
                        self.log_result(f"Distance Calculation: {test['route']}", True, response_time,
                                      f"API: {api_distance:.0f} nm, Expected: {expected} nm")
                    else:
                        self.log_result(f"Distance Calculation: {test['route']}", False, response_time,
                                      f"API: {api_distance:.0f} nm, Expected: {expected} nm (diff: {abs(api_distance-expected):.0f})")
                else:
                    self.log_result(f"Distance Calculation: {test['route']}", False, response_time,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Distance Calculation: {test['route']}", False, 0, f"Error: {e}")

    def test_route_optimization(self):
        """Test route optimization algorithms"""
        try:
            start_time = time.time()
            
            payload = {
                "start_port": {"lat": 1.3521, "lon": 103.8198},   # Singapore
                "end_port": {"lat": 51.9244, "lon": 4.4777},      # Rotterdam
                "optimization_criteria": {
                    "fuel_efficiency": 0.4,
                    "time_efficiency": 0.3,
                    "weather_safety": 0.3
                },
                "vessel_specifications": {
                    "type": "container",
                    "length": 400,
                    "beam": 59,
                    "draft": 16,
                    "service_speed": 22
                }
            }
            
            response = requests.post(f"{BASE_URL}/routing/optimize",
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['optimized_route', 'fuel_consumption', 'total_cost']
                if all(field in data for field in required_fields):
                    fuel_consumption = data['fuel_consumption']
                    total_cost = data['total_cost']
                    
                    self.log_result("Route Optimization", True, response_time,
                                  f"Fuel: {fuel_consumption:.0f} tons, Cost: ${total_cost:,.0f}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Route Optimization", False, response_time,
                                  f"Missing fields: {missing}")
            else:
                self.log_result("Route Optimization", False, response_time,
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Route Optimization", False, 0, f"Error: {e}")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🗺️ MARITIME ROUTING FUNCTIONALITY TEST RESULTS")
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
        
        print("\n🗺️ TESTED FUNCTIONALITY:")
        print("   • Basic route planning between major ports")
        print("   • Land avoidance algorithms")
        print("   • Weather-optimized routing")
        print("   • Multi-waypoint route optimization")
        print("   • Different route types (shortest, fastest, economical, safe)")
        print("   • Navigation safety features")
        print("   • Distance calculation accuracy")
        print("   • Route optimization with vessel specifications")
        
        if passed_tests == total_tests:
            print("\n🎉 RESULT: MARITIME ROUTING FUNCTIONALITY IS PERFECT! 🎉")
        elif passed_tests >= total_tests * 0.8:
            print("\n✅ RESULT: MARITIME ROUTING FUNCTIONALITY IS MOSTLY WORKING")
        else:
            print("\n⚠️ RESULT: MARITIME ROUTING NEEDS ATTENTION")
        
        print("="*80)

def main():
    print("🗺️ MARITIME ASSISTANT - MARITIME ROUTING TESTING")
    print("=" * 60)
    print("Testing comprehensive maritime routing functionality...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 60)
    
    suite = MaritimeRoutingTestSuite()
    
    # Run all tests
    if suite.test_server_connection():
        suite.test_basic_route_planning()
        suite.test_land_avoidance()
        suite.test_weather_routing()
        suite.test_multi_waypoint_routing()
        suite.test_route_types()
        suite.test_navigation_safety()
        suite.test_distance_calculations()
        suite.test_route_optimization()
    else:
        print("❌ Server not responding. Please ensure the backend server is running.")
        return
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
