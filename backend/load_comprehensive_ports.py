#!/usr/bin/env python3
"""
Comprehensive Ports Database Loader
Loads 4000+ ports into the maritime assistant database
"""

import asyncio
import sys
import os
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ports_service import PortsService
from maritime_ports_api import MaritimePortsAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def load_comprehensive_ports():
    """Load comprehensive ports database"""
    print("🚢 Maritime Assistant - Comprehensive Ports Database Loader")
    print("=" * 60)
    
    # Initialize services
    ports_service = PortsService()
    maritime_api = MaritimePortsAPI()
    
    # Check current database status
    current_count = ports_service.get_ports_count()
    print(f"📊 Current ports in database: {current_count}")
    
    # Load comprehensive ports from API
    print("\n🌍 Loading comprehensive world ports...")
    try:
        comprehensive_ports = await maritime_api.get_comprehensive_ports_data()
        print(f"✅ Retrieved {len(comprehensive_ports)} comprehensive ports")
        
        # Show sample of ports
        print(f"\n📋 Sample of comprehensive ports:")
        for i, port in enumerate(comprehensive_ports[:15]):
            print(f"  {i+1:2d}. {port['name']} ({port['country']}) - {port.get('type', 'General')}")
        
        if len(comprehensive_ports) > 15:
            print(f"  ... and {len(comprehensive_ports) - 15} more ports")
        
        # Load into database
        print(f"\n💾 Loading {len(comprehensive_ports)} ports into database...")
        loaded_count = await ports_service.load_comprehensive_ports_from_api()
        
        print(f"✅ Successfully loaded {loaded_count} comprehensive ports!")
        
        # Verify database update
        new_count = ports_service.get_ports_count()
        print(f"📊 New total ports in database: {new_count}")
        
        # Test search functionality
        print(f"\n🔍 Testing search functionality:")
        test_searches = ["Mumbai", "Shanghai", "Rotterdam", "Singapore", "Los Angeles", "Kolkata"]
        
        for search_term in test_searches:
            results = await ports_service.search_ports(search_term, limit=3)
            if results:
                print(f"  ✅ '{search_term}': Found {len(results)} port(s)")
                for result in results[:2]:
                    print(f"      - {result['name']} ({result['country']})")
            else:
                print(f"  ❌ '{search_term}': No results found")
        
        # Get database statistics
        print(f"\n📈 Database Statistics:")
        stats = await ports_service.get_port_statistics()
        print(f"  Total Ports: {stats['total_ports']}")
        print(f"  Average Depth: {stats['average_depth']}m")
        print(f"  Top 5 Countries by Ports:")
        for country_stat in stats['ports_by_country'][:5]:
            print(f"    - {country_stat['country']}: {country_stat['count']} ports")
        print(f"  Port Types:")
        for type_stat in stats['ports_by_type'][:5]:
            print(f"    - {type_stat['type']}: {type_stat['count']} ports")
        
        # Show countries with ports
        countries = ports_service.get_countries_with_ports()
        print(f"  Countries with Ports: {len(countries)}")
        print(f"  Sample Countries: {', '.join(countries[:10])}")
        
        print(f"\n🎉 Comprehensive ports database successfully loaded!")
        print(f"💡 Your Maritime Assistant now supports {new_count} ports worldwide!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading comprehensive ports: {str(e)}")
        return False

async def test_port_functionality():
    """Test various port functionality"""
    print(f"\n🧪 Testing Port Functionality:")
    print("=" * 40)
    
    ports_service = PortsService()
    
    # Test nearby ports
    print("🗺️ Testing nearby ports (around Singapore):")
    nearby = await ports_service.get_nearby_ports(1.2966, 103.8006, radius_km=200, limit=5)
    for port in nearby:
        print(f"  - {port['name']} ({port['country']}) - {port.get('distance_km', 0):.1f}km")
    
    # Test ports by type
    print(f"\n🏗️ Testing ports by type (Container ports):")
    container_ports = await ports_service.get_ports_by_type("Container", limit=10)
    for port in container_ports[:5]:
        print(f"  - {port['name']} ({port['country']})")
    
    # Test ports by country
    print(f"\n🇺🇸 Testing ports by country (India):")
    india_ports = await ports_service.get_ports_by_country("India", limit=10)
    for port in india_ports[:5]:
        print(f"  - {port['name']} - {port['type']}")
    
    print(f"✅ Port functionality tests completed!")

if __name__ == "__main__":
    print("🌊 Starting Comprehensive Ports Database Setup...")
    
    async def main():
        success = await load_comprehensive_ports()
        if success:
            await test_port_functionality()
        else:
            print("❌ Failed to load comprehensive ports database")
            sys.exit(1)
    
    asyncio.run(main())
