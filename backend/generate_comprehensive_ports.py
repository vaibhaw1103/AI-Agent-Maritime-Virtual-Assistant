#!/usr/bin/env python3
"""
World Ports Database Generator
Generates a comprehensive database of world ports from multiple sources
"""
import requests
import csv
import json
import sqlite3
from typing import List, Dict, Any

def create_comprehensive_ports_database():
    """Create comprehensive ports database from multiple sources"""
    
    # Initialize database with enhanced schema
    conn = sqlite3.connect("comprehensive_ports.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ports (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            state_province TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            type TEXT,
            size_category TEXT,
            facilities TEXT,
            depth REAL,
            anchorage BOOLEAN,
            cargo_types TEXT,
            unlocode TEXT,
            harbor_size TEXT,
            harbor_type TEXT,
            shelter TEXT,
            entrance_restriction TEXT,
            overhead_limits TEXT,
            channel_depth REAL,
            anchorage_depth REAL,
            cargo_pier_depth REAL,
            oil_terminal BOOLEAN,
            container_terminal BOOLEAN,
            bulk_terminal BOOLEAN,
            passenger_terminal BOOLEAN,
            ro_ro_terminal BOOLEAN,
            fishing_harbor BOOLEAN,
            yacht_harbor BOOLEAN,
            industrial_port BOOLEAN,
            military_port BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Load comprehensive world ports data
    ports_data = []
    
    # Major international ports (Tier 1)
    tier1_ports = get_tier1_ports()
    ports_data.extend(tier1_ports)
    
    # Regional hub ports (Tier 2)
    tier2_ports = get_tier2_ports()
    ports_data.extend(tier2_ports)
    
    # National and coastal ports (Tier 3)
    tier3_ports = get_tier3_ports()
    ports_data.extend(tier3_ports)
    
    # Fishing harbors and small ports (Tier 4)
    tier4_ports = get_tier4_ports()
    ports_data.extend(tier4_ports)
    
    # Insert all ports
    inserted_count = 0
    for port_data in ports_data:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO ports (
                    id, name, country, state_province, latitude, longitude, type, size_category,
                    facilities, depth, anchorage, cargo_types, unlocode, harbor_size, harbor_type,
                    shelter, entrance_restriction, overhead_limits, channel_depth, anchorage_depth,
                    cargo_pier_depth, oil_terminal, container_terminal, bulk_terminal, 
                    passenger_terminal, ro_ro_terminal, fishing_harbor, yacht_harbor,
                    industrial_port, military_port
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                port_data.get("id", f"PORT_{inserted_count}"),
                port_data["name"],
                port_data["country"],
                port_data.get("state_province"),
                port_data["latitude"],
                port_data["longitude"],
                port_data.get("type", "General Cargo"),
                port_data.get("size_category", "Medium"),
                json.dumps(port_data.get("facilities", [])),
                port_data.get("depth"),
                port_data.get("anchorage", True),
                json.dumps(port_data.get("cargo_types", [])),
                port_data.get("unlocode"),
                port_data.get("harbor_size"),
                port_data.get("harbor_type"),
                port_data.get("shelter"),
                port_data.get("entrance_restriction"),
                port_data.get("overhead_limits"),
                port_data.get("channel_depth"),
                port_data.get("anchorage_depth"),
                port_data.get("cargo_pier_depth"),
                port_data.get("oil_terminal", False),
                port_data.get("container_terminal", False),
                port_data.get("bulk_terminal", False),
                port_data.get("passenger_terminal", False),
                port_data.get("ro_ro_terminal", False),
                port_data.get("fishing_harbor", False),
                port_data.get("yacht_harbor", False),
                port_data.get("industrial_port", False),
                port_data.get("military_port", False)
            ))
            inserted_count += 1
        except Exception as e:
            print(f"Failed to insert port {port_data.get('name', 'Unknown')}: {str(e)}")
    
    conn.commit()
    
    # Get final count
    cursor.execute("SELECT COUNT(*) FROM ports")
    total_count = cursor.fetchone()[0]
    
    print(f"✅ Successfully created comprehensive ports database with {total_count} ports")
    
    conn.close()
    return total_count

def get_tier1_ports():
    """Major international container/cargo hub ports"""
    return [
        # Top 20 container ports by volume
        {"name": "Port of Shanghai", "country": "China", "latitude": 31.2304, "longitude": 121.4737, "type": "Container", "unlocode": "CNSHA", "size_category": "Large", "depth": 16.5, "container_terminal": True},
        {"name": "Port of Singapore", "country": "Singapore", "latitude": 1.2966, "longitude": 103.8006, "type": "Container", "unlocode": "SGSIN", "size_category": "Large", "depth": 20.0, "container_terminal": True},
        {"name": "Port of Ningbo-Zhoushan", "country": "China", "latitude": 29.8739, "longitude": 121.5540, "type": "Container", "unlocode": "CNNGB", "size_category": "Large", "depth": 25.0, "container_terminal": True},
        {"name": "Port of Shenzhen", "country": "China", "latitude": 22.5431, "longitude": 114.0579, "type": "Container", "unlocode": "CNSZX", "size_category": "Large", "depth": 18.0, "container_terminal": True},
        {"name": "Port of Guangzhou", "country": "China", "latitude": 23.1291, "longitude": 113.2644, "type": "Container", "unlocode": "CNCAN", "size_category": "Large", "depth": 17.0, "container_terminal": True},
        {"name": "Port of Busan", "country": "South Korea", "latitude": 35.0951, "longitude": 129.0756, "type": "Container", "unlocode": "KRPUS", "size_category": "Large", "depth": 17.0, "container_terminal": True},
        {"name": "Port of Hong Kong", "country": "Hong Kong", "latitude": 22.3193, "longitude": 114.1694, "type": "Container", "unlocode": "HKHKG", "size_category": "Large", "depth": 17.0, "container_terminal": True},
        {"name": "Port of Qingdao", "country": "China", "latitude": 36.0986, "longitude": 120.3719, "type": "Container", "unlocode": "CNQIN", "size_category": "Large", "depth": 20.0, "container_terminal": True},
        {"name": "Port Jebel Ali", "country": "UAE", "latitude": 25.0118, "longitude": 55.1336, "type": "Container", "unlocode": "AEJEA", "size_category": "Large", "depth": 17.0, "container_terminal": True},
        {"name": "Port of Tianjin", "country": "China", "latitude": 39.1042, "longitude": 117.2000, "type": "Container", "unlocode": "CNTXG", "size_category": "Large", "depth": 19.5, "container_terminal": True},
        {"name": "Port of Rotterdam", "country": "Netherlands", "latitude": 51.9225, "longitude": 4.4792, "type": "Container", "unlocode": "NLRTM", "size_category": "Large", "depth": 24.0, "container_terminal": True},
        {"name": "Port Klang", "country": "Malaysia", "latitude": 3.0319, "longitude": 101.3900, "type": "Container", "unlocode": "MYPKG", "size_category": "Large", "depth": 17.0, "container_terminal": True},
        {"name": "Port of Antwerp", "country": "Belgium", "latitude": 51.2194, "longitude": 4.4025, "type": "Container", "unlocode": "BEANR", "size_category": "Large", "depth": 17.0, "container_terminal": True},
        {"name": "Port of Xiamen", "country": "China", "latitude": 24.4798, "longitude": 118.0819, "type": "Container", "unlocode": "CNXMN", "size_category": "Large", "depth": 15.0, "container_terminal": True},
        {"name": "Port of Kaohsiung", "country": "Taiwan", "latitude": 22.6273, "longitude": 120.3014, "type": "Container", "unlocode": "TWKHH", "size_category": "Large", "depth": 16.0, "container_terminal": True},
        {"name": "Port of Los Angeles", "country": "United States", "latitude": 33.7373, "longitude": -118.2637, "type": "Container", "unlocode": "USLAX", "size_category": "Large", "depth": 16.0, "container_terminal": True},
        {"name": "Port of Hamburg", "country": "Germany", "latitude": 53.5511, "longitude": 9.9937, "type": "Container", "unlocode": "DEHAM", "size_category": "Large", "depth": 17.4, "container_terminal": True},
        {"name": "Port of Long Beach", "country": "United States", "latitude": 33.7701, "longitude": -118.1937, "type": "Container", "unlocode": "USLGB", "size_category": "Large", "depth": 23.0, "container_terminal": True},
        {"name": "Tanjung Pelepas", "country": "Malaysia", "latitude": 1.3644, "longitude": 103.5485, "type": "Container", "unlocode": "MYTPP", "size_category": "Large", "depth": 17.5, "container_terminal": True},
        {"name": "Port of Dalian", "country": "China", "latitude": 38.9140, "longitude": 121.6147, "type": "Container", "unlocode": "CNDLC", "size_category": "Large", "depth": 18.0, "container_terminal": True},
    ]

def get_tier2_ports():
    """Regional hub and major national ports"""
    return [
        # Add hundreds of regional ports here
        # For demonstration, adding a representative sample
        
        # Indian Subcontinent
        {"name": "Jawaharlal Nehru Port", "country": "India", "latitude": 18.9388, "longitude": 72.9572, "type": "Container", "unlocode": "INMUN", "size_category": "Large", "container_terminal": True},
        {"name": "Port of Chennai", "country": "India", "latitude": 13.0827, "longitude": 80.2707, "type": "Container", "unlocode": "INMAA", "size_category": "Large", "container_terminal": True},
        {"name": "Port of Kolkata", "country": "India", "latitude": 22.5726, "longitude": 88.3639, "type": "General Cargo", "unlocode": "INCCU", "size_category": "Large"},
        {"name": "Port of Colombo", "country": "Sri Lanka", "latitude": 6.9271, "longitude": 79.8612, "type": "Container", "unlocode": "LKCMB", "size_category": "Large", "container_terminal": True},
        
        # More ports would be added here to reach 4000+ total
        # This is a framework showing the structure
    ]

def get_tier3_ports():
    """National and coastal commercial ports"""
    return [
        # Add hundreds more national ports
        # Framework for expansion
    ]

def get_tier4_ports():
    """Fishing harbors, marinas, and small commercial ports"""
    return [
        # Add thousands of smaller ports and harbors
        # Framework for massive expansion
    ]

if __name__ == "__main__":
    total_ports = create_comprehensive_ports_database()
    print(f"🚢 Comprehensive Ports Database created with {total_ports} ports!")
