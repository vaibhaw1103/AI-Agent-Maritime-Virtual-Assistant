#!/usr/bin/env python3
"""
Test the fixed port weather endpoint
"""

import requests
import json

def test_port_weather():
    """Test the port weather endpoint"""
    
    print('🌦️ Testing port weather endpoint...')
    
    try:
        # Test the kolkata port weather
        response = requests.get('http://127.0.0.1:8000/port-weather/kolkata')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ Port weather endpoint working!')
            print(f'📍 Port: {data["port"]["name"]}')
            print(f'🌍 Coordinates: {data["port"]["coordinates"]}')
            print(f'🌤️ Weather: {data["weather"]["current_weather"]["conditions"]}')
            print(f'🌡️ Temperature: {data["weather"]["current_weather"]["temperature"]}°C')
            print(f'🌊 Wave Height: {data["weather"]["marine_conditions"]["wave_height"]}m')
            return True
        else:
            print(f'❌ Error: {response.status_code}')
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print('❌ Connection error: Backend server not running')
        print('Please start the backend server first: python main.py')
        return False
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
        return False

def test_other_ports():
    """Test other major ports"""
    
    test_ports = ['singapore', 'shanghai', 'rotterdam', 'hamburg']
    
    print('\n🌍 Testing other major ports...')
    for port in test_ports:
        try:
            response = requests.get(f'http://127.0.0.1:8000/port-weather/{port}')
            if response.status_code == 200:
                data = response.json()
                temp = data["weather"]["current_weather"]["temperature"]
                conditions = data["weather"]["current_weather"]["conditions"]
                print(f'✅ {port.title()}: {temp}°C, {conditions}')
            else:
                print(f'❌ {port.title()}: Error {response.status_code}')
        except Exception as e:
            print(f'❌ {port.title()}: {str(e)[:50]}...')

if __name__ == "__main__":
    success = test_port_weather()
    if success:
        test_other_ports()
        print('\n🎉 All port weather tests completed!')
    else:
        print('\n⚠️ Port weather endpoint needs fixing or server is not running')
