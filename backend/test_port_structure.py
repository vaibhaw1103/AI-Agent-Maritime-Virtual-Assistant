#!/usr/bin/env python3
"""
Test port data structure
"""

import asyncio
from ports_service import PortsService

async def test_port_data():
    try:
        service = PortsService()
        ports = await service.search_ports('kolkata', limit=1)
        
        print("🔍 Testing port data structure...")
        if ports:
            port = ports[0]
            print("📊 Port data structure:")
            for key, value in port.items():
                print(f"   {key}: {value}")
            print()
            print("✅ Keys available:", list(port.keys()))
        else:
            print("❌ No ports found for 'kolkata'")
            
            # Try getting any port
            all_ports = await service.get_all_ports(limit=1)
            if all_ports:
                port = all_ports[0]
                print("📊 Sample port data structure:")
                for key, value in port.items():
                    print(f"   {key}: {value}")
                print()
                print("✅ Keys available:", list(port.keys()))
            else:
                print("❌ No ports in database at all")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_port_data())
