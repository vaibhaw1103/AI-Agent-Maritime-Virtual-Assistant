#!/usr/bin/env python3
"""
Quick script to test ports database
"""
import asyncio
import sys
from ports_service import PortsService

async def test_ports():
    """Test ports functionality"""
    print("Testing ports database...")
    
    ports_service = PortsService()
    
    # Test basic functionality
    count = ports_service.get_ports_count()
    print(f"Total ports in database: {count}")
    
    # Test search for Kolkata
    print("\n=== Searching for 'kolkata' ===")
    kolkata_results = await ports_service.search_ports("kolkata")
    print(f"Kolkata search results: {len(kolkata_results)} found")
    for port in kolkata_results:
        print(f"  - {port.get('name', 'Unknown')} ({port.get('country', 'Unknown')})")
    
    # Test search for Calcutta (alternative name)
    print("\n=== Searching for 'calcutta' ===")
    calcutta_results = await ports_service.search_ports("calcutta")
    print(f"Calcutta search results: {len(calcutta_results)} found")
    for port in calcutta_results:
        print(f"  - {port.get('name', 'Unknown')} ({port.get('country', 'Unknown')})")
    
    # Test search for India ports
    print("\n=== Searching for 'india' ===")
    india_results = await ports_service.search_ports("india", limit=5)
    print(f"India search results: {len(india_results)} found")
    for port in india_results:
        print(f"  - {port.get('name', 'Unknown')} ({port.get('country', 'Unknown')})")
    
    # Show first 10 ports
    print("\n=== First 10 ports in database ===")
    all_ports = await ports_service.get_all_ports(limit=10)
    for port in all_ports:
        print(f"  - {port.get('name', 'Unknown')} ({port.get('country', 'Unknown')})")

if __name__ == "__main__":
    asyncio.run(test_ports())
