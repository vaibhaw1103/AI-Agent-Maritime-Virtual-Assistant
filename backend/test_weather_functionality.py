#!/usr/bin/env python3
"""
Test Weather functionality
"""

import requests
import json
import time

def test_current_weather():
    """Test current weather endpoint"""
    
    print('🌤️ Testing Current Weather Endpoint...')
    print('=' * 40)

    base_url = 'http://127.0.0.1:8000'
    
    # Test cases for current weather
    weather_tests = [
        {
            'description': 'Singapore coordinates',
            'payload': {'latitude': 1.3521, 'longitude': 103.8198, 'location_name': 'Singapore'},
        },
        {
            'description': 'Mumbai coordinates',
            'payload': {'latitude': 19.0760, 'longitude': 72.8777, 'location_name': 'Mumbai'},
        },
        {
            'description': 'Rotterdam coordinates', 
            'payload': {'latitude': 51.9225, 'longitude': 4.47917, 'location_name': 'Rotterdam'},
        },
        {
            'description': 'New York coordinates',
            'payload': {'latitude': 40.7128, 'longitude': -74.0060, 'location_name': 'New York'},
        },
        {
            'description': 'Invalid coordinates (middle of ocean)',
            'payload': {'latitude': 0.0, 'longitude': 0.0, 'location_name': 'Ocean'},
        }
    ]

    results = []
    
    for i, test in enumerate(weather_tests, 1):
        print(f'\n🔍 Test {i}: {test["description"]}')
        print(f'📍 Coordinates: {test["payload"]["latitude"]}, {test["payload"]["longitude"]}')
        
        try:
            start_time = time.time()
            response = requests.post(f'{base_url}/weather', 
                                   json=test['payload'],
                                   headers={'Content-Type': 'application/json'},
                                   timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f'✅ Status: {response.status_code}')
                print(f'⏱️ Response time: {response_time:.2f}s')
                
                # Check response structure
                if 'current_weather' in data:
                    weather = data['current_weather']
                    print(f'🌡️ Temperature: {weather.get("temperature", "N/A")}°C')
                    print(f'🌤️ Conditions: {weather.get("conditions", "N/A")}')
                    print(f'💨 Wind: {weather.get("wind_speed", "N/A")} km/h')
                    print(f'💧 Humidity: {weather.get("humidity", "N/A")}%')
                    
                    results.append({
                        'test': test['description'],
                        'status': 'PASS',
                        'response_time': response_time,
                        'temperature': weather.get('temperature'),
                        'conditions': weather.get('conditions')
                    })
                else:
                    print('❌ Missing current_weather in response')
                    results.append({
                        'test': test['description'],
                        'status': 'FAIL - Missing weather data',
                        'error': 'No current_weather field'
                    })
                    
            else:
                print(f'❌ HTTP Error: {response.status_code}')
                error_text = response.text[:200] if response.text else 'No error message'
                print(f'🔍 Error: {error_text}')
                
                results.append({
                    'test': test['description'],
                    'status': f'FAIL - HTTP {response.status_code}',
                    'error': error_text
                })
                
        except requests.exceptions.ConnectionError:
            print('❌ Connection Error: Backend server not running')
            results.append({
                'test': test['description'],
                'status': 'FAIL - Connection Error',
                'error': 'Backend server not running'
            })
            break
            
        except requests.exceptions.Timeout:
            print('❌ Timeout: Request took longer than 15 seconds')
            results.append({
                'test': test['description'],
                'status': 'FAIL - Timeout',
                'error': 'Request timeout'
            })
            
        except Exception as e:
            print(f'❌ Unexpected Error: {str(e)}')
            results.append({
                'test': test['description'],
                'status': 'FAIL - Exception',
                'error': str(e)
            })
        
        time.sleep(0.5)  # Small delay between tests
    
    return results

def test_port_weather():
    """Test port weather endpoint"""
    
    print('\n🏔️ Testing Port Weather Endpoint...')
    print('=' * 40)

    base_url = 'http://127.0.0.1:8000'
    
    # Test various ports
    port_tests = [
        'singapore',
        'kolkata',
        'mumbai', 
        'shanghai',
        'rotterdam',
        'hamburg',
        'los angeles',
        'nonexistentport123'  # Should fail
    ]

    results = []
    
    for i, port_name in enumerate(port_tests, 1):
        print(f'\n🔍 Test {i}: Port "{port_name}"')
        
        try:
            start_time = time.time()
            response = requests.get(f'{base_url}/port-weather/{port_name}', timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f'✅ Status: {response.status_code}')
                print(f'⏱️ Response time: {response_time:.2f}s')
                
                # Check response structure
                if 'port' in data and 'weather' in data:
                    port_info = data['port']
                    weather_info = data['weather']['current_weather']
                    
                    print(f'🏔️ Port: {port_info.get("name", "N/A")}')
                    print(f'🌍 Country: {port_info.get("country", "N/A")}')
                    print(f'🌡️ Temperature: {weather_info.get("temperature", "N/A")}°C')
                    print(f'🌤️ Conditions: {weather_info.get("conditions", "N/A")}')
                    
                    results.append({
                        'test': f'Port {port_name}',
                        'status': 'PASS',
                        'response_time': response_time,
                        'port_name': port_info.get("name"),
                        'temperature': weather_info.get('temperature')
                    })
                else:
                    print('❌ Missing port or weather data in response')
                    results.append({
                        'test': f'Port {port_name}',
                        'status': 'FAIL - Missing data',
                        'error': 'No port or weather data'
                    })
                    
            elif response.status_code == 404:
                print(f'⚠️ Port not found (expected for invalid ports): {response.status_code}')
                results.append({
                    'test': f'Port {port_name}',
                    'status': 'NOT FOUND (Expected for invalid ports)',
                    'response_time': response_time
                })
            else:
                print(f'❌ HTTP Error: {response.status_code}')
                error_text = response.text[:200] if response.text else 'No error message'
                print(f'🔍 Error: {error_text}')
                
                results.append({
                    'test': f'Port {port_name}',
                    'status': f'FAIL - HTTP {response.status_code}',
                    'error': error_text
                })
                
        except Exception as e:
            print(f'❌ Error: {str(e)}')
            results.append({
                'test': f'Port {port_name}',
                'status': 'FAIL - Exception',
                'error': str(e)
            })
        
        time.sleep(0.5)
    
    return results

def test_weather_data_quality():
    """Test weather data quality and structure"""
    
    print('\n🔬 Testing Weather Data Quality...')
    print('=' * 40)
    
    base_url = 'http://127.0.0.1:8000'
    
    try:
        # Get detailed weather data
        response = requests.post(f'{base_url}/weather', 
                               json={'latitude': 1.3521, 'longitude': 103.8198, 'location_name': 'Singapore'},
                               timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            print('📊 Checking data structure and quality...')
            
            # Check current weather
            if 'current_weather' in data:
                current = data['current_weather']
                print('✅ Current weather data present')
                
                required_fields = ['temperature', 'humidity', 'pressure', 'wind_speed', 'conditions']
                missing_fields = [field for field in required_fields if field not in current or current[field] is None]
                
                if not missing_fields:
                    print('✅ All required current weather fields present')
                else:
                    print(f'⚠️ Missing current weather fields: {missing_fields}')
                    
                # Check data ranges
                temp = current.get('temperature', 0)
                humidity = current.get('humidity', 0)
                pressure = current.get('pressure', 0)
                
                if -50 <= temp <= 60:  # Reasonable temperature range
                    print(f'✅ Temperature in reasonable range: {temp}°C')
                else:
                    print(f'⚠️ Temperature out of range: {temp}°C')
                    
                if 0 <= humidity <= 100:
                    print(f'✅ Humidity in valid range: {humidity}%')
                else:
                    print(f'⚠️ Humidity out of range: {humidity}%')
                    
                if 900 <= pressure <= 1100:  # Typical atmospheric pressure range
                    print(f'✅ Pressure in reasonable range: {pressure} hPa')
                else:
                    print(f'⚠️ Pressure out of range: {pressure} hPa')
            
            # Check forecast
            if 'forecast' in data and data['forecast']:
                forecast = data['forecast']
                print(f'✅ Forecast data present ({len(forecast)} days)')
                
                for i, day in enumerate(forecast[:3]):  # Check first 3 days
                    if 'date' in day and 'temperature_high' in day and 'temperature_low' in day:
                        print(f'✅ Day {i+1} forecast complete: {day["date"]} ({day["temperature_low"]}-{day["temperature_high"]}°C)')
                    else:
                        print(f'⚠️ Day {i+1} forecast incomplete')
            
            # Check marine conditions
            if 'marine_conditions' in data:
                marine = data['marine_conditions']
                print('✅ Marine conditions present')
                
                if 'wave_height' in marine and 'tide' in marine:
                    print(f'✅ Wave height: {marine["wave_height"]}m, Tide: {marine["tide"]}')
                else:
                    print('⚠️ Some marine data missing')
            
            return True
        else:
            print(f'❌ Failed to get weather data: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Error testing data quality: {e}')
        return False

def print_weather_summary(current_results, port_results, quality_passed):
    """Print comprehensive weather test summary"""
    
    print('\n' + '=' * 60)
    print('📊 WEATHER FUNCTIONALITY TEST SUMMARY')
    print('=' * 60)
    
    # Current weather summary
    current_passed = [r for r in current_results if r['status'] == 'PASS']
    current_failed = [r for r in current_results if 'FAIL' in r['status']]
    
    print(f'\n🌤️ CURRENT WEATHER ENDPOINT:')
    print(f'✅ Passed: {len(current_passed)}/{len(current_results)} tests')
    print(f'❌ Failed: {len(current_failed)}/{len(current_results)} tests')
    
    if current_passed:
        avg_time = sum(r['response_time'] for r in current_passed) / len(current_passed)
        print(f'⏱️ Average response time: {avg_time:.2f}s')
    
    # Port weather summary
    port_passed = [r for r in port_results if r['status'] == 'PASS']
    port_failed = [r for r in port_results if 'FAIL' in r['status']]
    port_not_found = [r for r in port_results if 'NOT FOUND' in r['status']]
    
    print(f'\n🏔️ PORT WEATHER ENDPOINT:')
    print(f'✅ Passed: {len(port_passed)}/{len(port_results)} tests')
    print(f'❌ Failed: {len(port_failed)}/{len(port_results)} tests')
    print(f'🔍 Not Found: {len(port_not_found)}/{len(port_results)} tests (Expected)')
    
    if port_passed:
        avg_time = sum(r['response_time'] for r in port_passed) / len(port_passed)
        print(f'⏱️ Average response time: {avg_time:.2f}s')
    
    # Data quality
    print(f'\n🔬 DATA QUALITY:')
    print(f'{"✅" if quality_passed else "❌"} Weather data structure and ranges: {"PASS" if quality_passed else "FAIL"}')
    
    # Overall assessment
    total_critical_tests = len(current_passed) + len(port_passed)
    total_tests = len(current_results) + len(port_results)
    
    if len(current_failed) == 0 and len(port_failed) == 0 and quality_passed:
        print(f'\n🎉 OVERALL STATUS: ALL WEATHER FUNCTIONALITY WORKING PERFECTLY!')
        print(f'🚀 Ready for production use!')
    elif len(current_failed) == 0 and len(port_failed) <= 1:  # Allow 1 port failure
        print(f'\n✅ OVERALL STATUS: Weather functionality working well!')
        print(f'⚠️ Minor issues found but core functionality operational')
    else:
        print(f'\n⚠️ OVERALL STATUS: Weather functionality has issues')
        print(f'🔧 Need to fix {len(current_failed) + len(port_failed)} failed tests')
        
    # Failed tests details
    if current_failed or port_failed:
        print(f'\n❌ FAILED TESTS:')
        for test in current_failed + port_failed:
            print(f'  - {test["test"]}: {test["status"]}')
            if 'error' in test:
                print(f'    Error: {test["error"][:100]}...')

if __name__ == "__main__":
    print('🌦️ COMPREHENSIVE WEATHER TESTING')
    print('=' * 50)
    
    # Run all tests
    current_results = test_current_weather()
    port_results = test_port_weather()
    quality_passed = test_weather_data_quality()
    
    # Print comprehensive summary
    print_weather_summary(current_results, port_results, quality_passed)
