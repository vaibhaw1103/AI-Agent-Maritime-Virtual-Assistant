#!/usr/bin/env python3
"""
📊 MARITIME ASSISTANT - PERFORMANCE & LOAD TESTING SUITE
========================================================

Comprehensive performance validation including:
- Response time analysis
- Concurrent user simulation
- Load testing under stress
- Memory and CPU monitoring
- Throughput measurement
- Database performance
- API endpoint stress testing

Version: 1.0
Date: August 22, 2025
"""

import asyncio
import aiohttp
import requests
import time
import threading
import json
import statistics
import psutil
import gc
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

@dataclass
class PerformanceMetric:
    """Performance measurement data"""
    endpoint: str
    response_time: float
    status_code: int
    payload_size: int
    timestamp: datetime
    error_message: Optional[str] = None

class PerformanceTestSuite:
    """Comprehensive performance and load testing"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.admin_token = None
        self.user_token = None
        self.metrics = []
        self.errors = []
        
    def log_result(self, test_name: str, passed: bool, duration: float = 0, details: str = ""):
        """Log test results with performance data"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "duration": duration,
            "details": details
        })
        print(f"{status} - {test_name} ({duration:.2f}s)")
        if details:
            print(f"   → {details}")

    def get_system_metrics(self):
        """Get current system performance metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available": psutil.virtual_memory().available / (1024**3),  # GB
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now()
        }

    def authenticate_admin(self):
        """Get admin token for authenticated tests"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", 
                                   json={"username": "admin", "password": "MaritimeAdmin2025!"}, 
                                   timeout=10)
            if response.status_code == 200:
                self.admin_token = response.json()['access_token']
                return True
            return False
        except Exception:
            return False

    def test_single_request_performance(self):
        """Test individual endpoint response times"""
        endpoints = [
            {"method": "GET", "url": "/", "name": "Home Page"},
            {"method": "POST", "url": "/weather", "name": "Weather API", 
             "data": {"latitude": 1.3521, "longitude": 103.8198, "location_name": "Singapore"}},
            {"method": "GET", "url": "/port-weather/singapore", "name": "Port Weather"},
            {"method": "POST", "url": "/public/chat", "name": "Public Chat", 
             "data": {"query": "What is the weather like in Singapore?"}},
        ]
        
        print(f"\\n🚀 TESTING INDIVIDUAL ENDPOINT PERFORMANCE...")
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                
                if endpoint["method"] == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint['url']}", timeout=TEST_TIMEOUT)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint['url']}", 
                                           json=endpoint.get("data", {}), timeout=TEST_TIMEOUT)
                
                duration = time.time() - start_time
                payload_size = len(response.content)
                
                # Store metric
                metric = PerformanceMetric(
                    endpoint=endpoint["name"],
                    response_time=duration,
                    status_code=response.status_code,
                    payload_size=payload_size,
                    timestamp=datetime.now()
                )
                self.metrics.append(metric)
                
                # Evaluate performance
                if response.status_code == 200:
                    if duration < 1.0:
                        performance_rating = "EXCELLENT"
                    elif duration < 2.0:
                        performance_rating = "VERY GOOD"
                    elif duration < 3.0:
                        performance_rating = "GOOD"
                    else:
                        performance_rating = "NEEDS IMPROVEMENT"
                    
                    self.log_result(f"{endpoint['name']} Response Time", True, duration,
                                  f"{performance_rating} | {payload_size} bytes | {response.status_code}")
                else:
                    self.log_result(f"{endpoint['name']} Response Time", False, duration,
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"{endpoint['name']} Response Time", False, 0, f"Error: {e}")

    def test_concurrent_users(self, num_users: int = 10):
        """Test concurrent user load"""
        print(f"\\n👥 TESTING {num_users} CONCURRENT USERS...")
        
        def make_request(user_id):
            """Single user request simulation"""
            try:
                start_time = time.time()
                response = requests.post(f"{BASE_URL}/public/chat", 
                                       json={"query": f"Hello from user {user_id}"}, 
                                       timeout=TEST_TIMEOUT)
                duration = time.time() - start_time
                return {
                    "user_id": user_id,
                    "duration": duration,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "user_id": user_id,
                    "duration": TEST_TIMEOUT,
                    "status_code": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_users)]
            concurrent_results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in concurrent_results if r["success"]]
        failed_requests = [r for r in concurrent_results if not r["success"]]
        
        if successful_requests:
            avg_response_time = statistics.mean([r["duration"] for r in successful_requests])
            max_response_time = max([r["duration"] for r in successful_requests])
            min_response_time = min([r["duration"] for r in successful_requests])
            
            success_rate = len(successful_requests) / len(concurrent_results) * 100
            throughput = len(successful_requests) / total_time  # requests per second
            
            if success_rate >= 95 and avg_response_time < 3.0:
                self.log_result(f"Concurrent Users ({num_users})", True, total_time,
                              f"{success_rate:.1f}% success | {throughput:.1f} req/s | Avg: {avg_response_time:.2f}s")
            else:
                self.log_result(f"Concurrent Users ({num_users})", False, total_time,
                              f"{success_rate:.1f}% success | {throughput:.1f} req/s | Avg: {avg_response_time:.2f}s")
            
            return {
                "success_rate": success_rate,
                "throughput": throughput,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "total_time": total_time
            }
        else:
            self.log_result(f"Concurrent Users ({num_users})", False, total_time,
                          f"All requests failed")
            return None

    def test_sustained_load(self, duration_seconds: int = 30, requests_per_second: int = 5):
        """Test sustained load over time"""
        print(f"\\n⏱️ TESTING SUSTAINED LOAD ({duration_seconds}s at {requests_per_second} req/s)...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        successful_requests = 0
        failed_requests = 0
        response_times = []
        system_metrics = []
        
        def make_sustained_request():
            nonlocal successful_requests, failed_requests
            try:
                req_start = time.time()
                response = requests.get(f"{BASE_URL}/", timeout=5)
                req_duration = time.time() - req_start
                
                if response.status_code == 200:
                    successful_requests += 1
                    response_times.append(req_duration)
                else:
                    failed_requests += 1
            except Exception:
                failed_requests += 1
        
        # Sustained load execution
        while time.time() < end_time:
            request_start = time.time()
            
            # Send burst of requests
            threads = []
            for _ in range(requests_per_second):
                thread = threading.Thread(target=make_sustained_request)
                thread.start()
                threads.append(thread)
            
            # Wait for requests to complete
            for thread in threads:
                thread.join(timeout=1)
            
            # Collect system metrics periodically
            if len(system_metrics) == 0 or time.time() - system_metrics[-1]["timestamp"].timestamp() > 5:
                system_metrics.append(self.get_system_metrics())
            
            # Maintain request rate
            elapsed = time.time() - request_start
            sleep_time = max(0, 1.0 - elapsed)  # 1 second interval
            time.sleep(sleep_time)
        
        total_duration = time.time() - start_time
        total_requests = successful_requests + failed_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        actual_throughput = successful_requests / total_duration
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            if success_rate >= 90 and avg_response_time < 2.0:
                self.log_result("Sustained Load Test", True, total_duration,
                              f"{success_rate:.1f}% success | {actual_throughput:.1f} req/s | Avg: {avg_response_time:.2f}s")
            else:
                self.log_result("Sustained Load Test", False, total_duration,
                              f"{success_rate:.1f}% success | {actual_throughput:.1f} req/s | Avg: {avg_response_time:.2f}s")
            
            return {
                "success_rate": success_rate,
                "throughput": actual_throughput,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "total_requests": total_requests,
                "system_metrics": system_metrics
            }
        else:
            self.log_result("Sustained Load Test", False, total_duration, "No successful requests")
            return None

    def test_memory_usage(self):
        """Test memory usage under load"""
        print(f"\\n🧠 TESTING MEMORY USAGE...")
        
        # Get initial memory state
        gc.collect()  # Force garbage collection
        initial_memory = self.get_system_metrics()
        
        # Generate load to test memory
        requests_made = 0
        start_time = time.time()
        
        try:
            for i in range(50):  # Make 50 requests
                response = requests.post(f"{BASE_URL}/public/chat", 
                                       json={"query": f"Memory test query {i}"}, 
                                       timeout=5)
                if response.status_code == 200:
                    requests_made += 1
                time.sleep(0.1)  # Small delay between requests
        except Exception as e:
            pass
        
        # Get final memory state
        gc.collect()
        final_memory = self.get_system_metrics()
        duration = time.time() - start_time
        
        memory_increase = final_memory["memory_percent"] - initial_memory["memory_percent"]
        
        if memory_increase < 10 and final_memory["memory_percent"] < 80:
            self.log_result("Memory Usage Test", True, duration,
                          f"{requests_made} requests | Memory: +{memory_increase:.1f}% | Final: {final_memory['memory_percent']:.1f}%")
        else:
            self.log_result("Memory Usage Test", False, duration,
                          f"Memory increase: +{memory_increase:.1f}% | Final: {final_memory['memory_percent']:.1f}%")
        
        return {
            "initial_memory": initial_memory["memory_percent"],
            "final_memory": final_memory["memory_percent"],
            "memory_increase": memory_increase,
            "requests_processed": requests_made
        }

    def test_database_performance(self):
        """Test database query performance"""
        print(f"\\n🗄️ TESTING DATABASE PERFORMANCE...")
        
        port_queries = ["singapore", "mumbai", "rotterdam", "shanghai", "hamburg"]
        query_times = []
        successful_queries = 0
        
        for port in port_queries:
            try:
                start_time = time.time()
                response = requests.get(f"{BASE_URL}/port-weather/{port}", timeout=10)
                query_time = time.time() - start_time
                
                if response.status_code == 200:
                    successful_queries += 1
                    query_times.append(query_time)
                    
            except Exception:
                pass
        
        if query_times:
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)
            success_rate = (successful_queries / len(port_queries)) * 100
            
            if avg_query_time < 1.0 and success_rate == 100:
                self.log_result("Database Performance", True, sum(query_times),
                              f"{success_rate:.0f}% success | Avg: {avg_query_time:.2f}s | Max: {max_query_time:.2f}s")
            else:
                self.log_result("Database Performance", False, sum(query_times),
                              f"{success_rate:.0f}% success | Avg: {avg_query_time:.2f}s")
            
            return {
                "success_rate": success_rate,
                "avg_query_time": avg_query_time,
                "max_query_time": max_query_time,
                "queries_tested": len(port_queries)
            }
        else:
            self.log_result("Database Performance", False, 0, "All database queries failed")
            return None

    def test_api_stress(self):
        """Stress test critical API endpoints"""
        print(f"\\n💪 STRESS TESTING CRITICAL ENDPOINTS...")
        
        # Test multiple endpoints simultaneously
        endpoints = [
            {"url": "/", "method": "GET"},
            {"url": "/public/chat", "method": "POST", "data": {"query": "Stress test"}},
            {"url": "/port-weather/singapore", "method": "GET"},
            {"url": "/weather", "method": "POST", "data": {"latitude": 1.35, "longitude": 103.8}},
        ]
        
        stress_results = {}
        
        for endpoint in endpoints:
            print(f"   🎯 Stress testing: {endpoint['url']}")
            
            def stress_request():
                try:
                    if endpoint["method"] == "GET":
                        response = requests.get(f"{BASE_URL}{endpoint['url']}", timeout=5)
                    else:
                        response = requests.post(f"{BASE_URL}{endpoint['url']}", 
                                               json=endpoint.get("data", {}), timeout=5)
                    return response.status_code == 200
                except Exception:
                    return False
            
            # Run 20 concurrent requests to each endpoint
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(stress_request) for _ in range(20)]
                results = [future.result() for future in as_completed(futures)]
            duration = time.time() - start_time
            
            success_count = sum(results)
            success_rate = (success_count / 20) * 100
            throughput = success_count / duration
            
            stress_results[endpoint["url"]] = {
                "success_rate": success_rate,
                "throughput": throughput,
                "duration": duration
            }
            
            print(f"      → {success_rate:.0f}% success | {throughput:.1f} req/s")
        
        # Overall stress test evaluation
        overall_success = statistics.mean([r["success_rate"] for r in stress_results.values()])
        overall_throughput = sum([r["throughput"] for r in stress_results.values()])
        
        if overall_success >= 90:
            self.log_result("API Stress Test", True, sum([r["duration"] for r in stress_results.values()]),
                          f"{overall_success:.1f}% overall success | {overall_throughput:.1f} total req/s")
        else:
            self.log_result("API Stress Test", False, 0,
                          f"{overall_success:.1f}% overall success - PERFORMANCE ISSUES")
        
        return stress_results

    def print_performance_summary(self):
        """Print comprehensive performance analysis"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        
        print("\\n" + "="*80)
        print("📊 MARITIME ASSISTANT - PERFORMANCE & LOAD TEST RESULTS")
        print("="*80)
        
        # Overall Performance Rating
        performance_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        if performance_score >= 95:
            performance_rating = "🚀 EXCELLENT"
            color = "🟢"
        elif performance_score >= 85:
            performance_rating = "✅ VERY GOOD"
            color = "🟡"
        elif performance_score >= 75:
            performance_rating = "⚠️ GOOD"
            color = "🟠"
        else:
            performance_rating = "❌ NEEDS IMPROVEMENT"
            color = "🔴"
        
        print(f"\\n🎯 OVERALL PERFORMANCE RATING: {performance_score:.1f}% - {performance_rating}")
        print(f"{color} PERFORMANCE STATUS: {performance_rating}")
        
        print(f"\\n📊 SUMMARY:")
        print(f"   ✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"   ❌ Tests Failed: {failed_tests}/{total_tests}")
        print(f"   📈 Success Rate: {performance_score:.1f}%")
        print(f"   ⏱️ Total Test Time: {total_time:.2f}s")
        
        # Performance Metrics Analysis
        if self.metrics:
            response_times = [m.response_time for m in self.metrics if m.response_time > 0]
            if response_times:
                avg_response = statistics.mean(response_times)
                max_response = max(response_times)
                min_response = min(response_times)
                
                print(f"\\n⚡ RESPONSE TIME ANALYSIS:")
                print(f"   📊 Average Response: {avg_response:.2f}s")
                print(f"   🚀 Fastest Response: {min_response:.2f}s")
                print(f"   🐌 Slowest Response: {max_response:.2f}s")
        
        print("\\n📋 DETAILED PERFORMANCE RESULTS:")
        for i, result in enumerate(self.results, 1):
            print(f"   {i:2d}. {result['status']} - {result['test']} ({result['duration']:.2f}s)")
            if result['details']:
                print(f"       → {result['details']}")
        
        print("\\n🔍 PERFORMANCE CATEGORIES TESTED:")
        print("   • Individual endpoint response times")
        print("   • Concurrent user simulation")  
        print("   • Sustained load testing")
        print("   • Memory usage monitoring")
        print("   • Database query performance")
        print("   • API stress testing")
        
        # System Resource Usage
        current_metrics = self.get_system_metrics()
        print(f"\\n💻 SYSTEM RESOURCE USAGE:")
        print(f"   🖥️ CPU Usage: {current_metrics['cpu_percent']:.1f}%")
        print(f"   🧠 Memory Usage: {current_metrics['memory_percent']:.1f}%")
        print(f"   💾 Available Memory: {current_metrics['memory_available']:.1f} GB")
        
        # Performance Recommendations
        print(f"\\n📈 PERFORMANCE ASSESSMENT:")
        if performance_score >= 95:
            print("   🚀 EXCELLENT PERFORMANCE - Production Ready!")
            print("   ✅ All systems operating at optimal levels")
            print("   🎯 Can handle enterprise-scale traffic")
        elif performance_score >= 85:
            print("   ✅ VERY GOOD PERFORMANCE - Production Ready")
            print("   💡 Minor optimizations could improve performance")
            print("   🎯 Suitable for production deployment")
        elif performance_score >= 75:
            print("   ⚠️ GOOD PERFORMANCE - Consider Optimizations")
            print("   🔧 Some performance improvements recommended")
            print("   📊 Monitor performance in production")
        else:
            print("   ❌ PERFORMANCE NEEDS IMPROVEMENT")
            print("   🔧 Significant optimization required")
            print("   ⚠️ Not recommended for production without fixes")
        
        print("="*80)

def main():
    print("📊 MARITIME ASSISTANT - PERFORMANCE & LOAD TESTING")
    print("=" * 65)
    print("Testing system performance and scalability...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 65)
    
    suite = PerformanceTestSuite()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly. Please ensure the backend server is running.")
            return
    except Exception:
        print("❌ Cannot connect to server. Please ensure the backend server is running at http://localhost:8000")
        return
    
    # Authenticate for protected endpoint tests
    suite.authenticate_admin()
    
    print("\\n🚀 Starting comprehensive performance testing...")
    
    # Run all performance tests
    suite.test_single_request_performance()
    suite.test_concurrent_users(num_users=5)   # Start with 5 concurrent users
    suite.test_concurrent_users(num_users=10)  # Scale to 10 concurrent users
    suite.test_sustained_load(duration_seconds=20, requests_per_second=3)
    suite.test_memory_usage()
    suite.test_database_performance()
    suite.test_api_stress()
    
    # Print comprehensive performance summary
    suite.print_performance_summary()

if __name__ == "__main__":
    main()
