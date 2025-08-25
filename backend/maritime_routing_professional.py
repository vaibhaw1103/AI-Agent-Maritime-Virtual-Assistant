"""
Professional Maritime Routing System for Hackathon Demo
Uses shoreline mask + graph routing approach with major sea waypoints
Avoids landmasses using preprocessed safe-sea-waypoint graph
"""

import math
import json
from typing import List, Tuple, Dict, Optional
from geopy.distance import geodesic
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

class ProfessionalMaritimeRouter:
    def __init__(self):
        """Initialize with major maritime waypoints and shipping lanes"""
        
        # Major maritime chokepoints and safe waypoints
        self.major_waypoints = {
            # Atlantic Ocean
            'gibraltar_strait': (36.1408, -5.3536),
            'english_channel_west': (49.3000, -5.0000),
            'english_channel_east': (51.0000, 2.0000),
            'north_sea_center': (55.0000, 4.0000),
            'norway_sea': (62.0000, 2.0000),
            'mid_atlantic_north': (45.0000, -40.0000),
            'mid_atlantic_south': (0.0000, -25.0000),
            'caribbean_east': (15.0000, -60.0000),
            'us_east_coast': (35.0000, -70.0000),
            
            # Mediterranean Sea
            'med_west': (40.0000, 3.0000),
            'med_central': (37.0000, 15.0000),
            'med_east': (34.0000, 28.0000),
            
            # Indian Ocean
            'suez_canal_med': (31.3000, 32.3000),
            'suez_canal_red': (29.9000, 32.5000),
            'red_sea_south': (12.5000, 43.5000),
            'arabian_sea': (15.0000, 65.0000),
            'indian_ocean_west': (-20.0000, 60.0000),
            'indian_ocean_central': (-10.0000, 75.0000),
            'indian_ocean_east': (-15.0000, 90.0000),
            'strait_of_hormuz': (26.5667, 56.2500),
            'persian_gulf': (27.0000, 51.0000),
            
            # Pacific Ocean
            'strait_of_malacca_west': (3.5000, 100.0000),
            'strait_of_malacca_east': (1.0000, 104.0000),
            'south_china_sea': (10.0000, 115.0000),
            'pacific_north_west': (45.0000, -130.0000),
            'pacific_north_east': (40.0000, -140.0000),
            'pacific_central': (0.0000, -150.0000),
            'pacific_south_west': (-20.0000, 170.0000),
            
            # Major Canals
            'panama_canal_atlantic': (9.3500, -79.9167),
            'panama_canal_pacific': (8.8833, -79.5667),
            
            # Cape Routes
            'cape_of_good_hope': (-34.3587, 18.4717),
            'cape_horn': (-55.9833, -67.2667),
            
            # Regional Hubs
            'singapore_strait': (1.2500, 103.8500),
            'tokyo_bay_approach': (35.0000, 140.0000),
            'hong_kong_approach': (22.0000, 114.5000),
            'rotterdam_approach': (52.0000, 4.0000),
            'hamburg_approach': (54.0000, 8.5000),
            'antwerp_approach': (51.5000, 3.8000)
        }
        
        # Define major landmasses as simplified polygons for intersection checking
        self.landmasses = {
            'europe': Polygon([
                (70, -10), (70, 40), (35, 40), (35, -10)
            ]),
            'africa': Polygon([
                (35, -20), (35, 55), (-35, 55), (-35, -20)
            ]),
            'asia': Polygon([
                (70, 40), (70, 180), (-10, 180), (-10, 40)
            ]),
            'north_america': Polygon([
                (70, -170), (70, -50), (15, -50), (15, -170)
            ]),
            'south_america': Polygon([
                (15, -90), (15, -35), (-60, -35), (-60, -90)
            ]),
            'australia': Polygon([
                (-10, 110), (-10, 155), (-45, 155), (-45, 110)
            ])
        }
        
        # Create navigation graph
        self.nav_graph = self._create_navigation_graph()
    
    def _create_navigation_graph(self) -> nx.Graph:
        """Create a graph of navigable waypoints connected by safe sea routes"""
        G = nx.Graph()
        
        # Add all waypoints as nodes
        for waypoint_id, (lat, lng) in self.major_waypoints.items():
            G.add_node(waypoint_id, lat=lat, lng=lng)
        
        # Connect waypoints that have safe sea routes between them
        # European routes
        european_connections = [
            ('rotterdam_approach', 'hamburg_approach'),
            ('rotterdam_approach', 'antwerp_approach'),
            ('rotterdam_approach', 'english_channel_east'),
            ('english_channel_east', 'english_channel_west'),
            ('english_channel_west', 'gibraltar_strait'),
            ('gibraltar_strait', 'med_west'),
            ('med_west', 'med_central'),
            ('med_central', 'med_east'),
            ('med_east', 'suez_canal_med'),
            ('hamburg_approach', 'north_sea_center'),
            ('north_sea_center', 'norway_sea'),
            ('north_sea_center', 'english_channel_east')
        ]
        
        # Atlantic routes
        atlantic_connections = [
            ('english_channel_west', 'mid_atlantic_north'),
            ('gibraltar_strait', 'mid_atlantic_north'),
            ('mid_atlantic_north', 'us_east_coast'),
            ('mid_atlantic_north', 'mid_atlantic_south'),
            ('mid_atlantic_south', 'caribbean_east'),
            ('caribbean_east', 'panama_canal_atlantic')
        ]
        
        # Indian Ocean routes
        indian_connections = [
            ('suez_canal_med', 'suez_canal_red'),
            ('suez_canal_red', 'red_sea_south'),
            ('red_sea_south', 'arabian_sea'),
            ('arabian_sea', 'strait_of_hormuz'),
            ('strait_of_hormuz', 'persian_gulf'),
            ('arabian_sea', 'indian_ocean_west'),
            ('indian_ocean_west', 'cape_of_good_hope'),
            ('indian_ocean_west', 'indian_ocean_central'),
            ('indian_ocean_central', 'indian_ocean_east'),
            ('indian_ocean_east', 'strait_of_malacca_west')
        ]
        
        # Pacific routes
        pacific_connections = [
            ('strait_of_malacca_west', 'strait_of_malacca_east'),
            ('strait_of_malacca_east', 'singapore_strait'),
            ('singapore_strait', 'south_china_sea'),
            ('south_china_sea', 'hong_kong_approach'),
            ('hong_kong_approach', 'tokyo_bay_approach'),
            ('tokyo_bay_approach', 'pacific_north_west'),
            ('pacific_north_west', 'pacific_north_east'),
            ('panama_canal_pacific', 'pacific_central'),
            ('pacific_central', 'pacific_south_west')
        ]
        
        # Canal connections
        canal_connections = [
            ('panama_canal_atlantic', 'panama_canal_pacific')
        ]
        
        # Add all connections with distances as weights
        all_connections = (european_connections + atlantic_connections + 
                         indian_connections + pacific_connections + canal_connections)
        
        for wp1, wp2 in all_connections:
            if wp1 in self.major_waypoints and wp2 in self.major_waypoints:
                lat1, lng1 = self.major_waypoints[wp1]
                lat2, lng2 = self.major_waypoints[wp2]
                distance = geodesic((lat1, lng1), (lat2, lng2)).nautical
                G.add_edge(wp1, wp2, weight=distance)
        
        return G
    
    def route_crosses_land(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """Check if a direct route between two points crosses land"""
        line = LineString([start[::-1], end[::-1]])  # (lng, lat) for shapely
        
        for landmass in self.landmasses.values():
            if line.intersects(landmass):
                return True
        return False
    
    def find_nearest_waypoint(self, point: Tuple[float, float]) -> str:
        """Find the nearest major waypoint to a given point"""
        min_distance = float('inf')
        nearest_waypoint = None
        
        for waypoint_id, waypoint_coords in self.major_waypoints.items():
            distance = geodesic(point, waypoint_coords).nautical
            if distance < min_distance:
                min_distance = distance
                nearest_waypoint = waypoint_id
        
        return nearest_waypoint
    
    def calculate_maritime_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Calculate professional maritime route avoiding landmasses
        Uses graph routing with major sea waypoints
        """
        print(f"Calculating professional maritime route from {origin} to {destination}")
        
        # Check if direct route crosses land
        if not self.route_crosses_land(origin, destination):
            print("Direct route is safe - using great circle")
            return self._create_direct_route(origin, destination)
        
        print("Direct route crosses land - using waypoint routing")
        
        # Find nearest waypoints to origin and destination
        start_waypoint = self.find_nearest_waypoint(origin)
        end_waypoint = self.find_nearest_waypoint(destination)
        
        print(f"Start waypoint: {start_waypoint}, End waypoint: {end_waypoint}")
        
        # Find shortest path through waypoint network
        try:
            waypoint_path = nx.shortest_path(self.nav_graph, start_waypoint, end_waypoint, weight='weight')
            print(f"Waypoint path: {waypoint_path}")
        except nx.NetworkXNoPath:
            print("No path found through waypoint network - using fallback")
            return self._create_fallback_route(origin, destination)
        
        # Convert waypoint path to coordinates
        route_points = [origin]
        
        for waypoint_id in waypoint_path:
            waypoint_coords = self.major_waypoints[waypoint_id]
            route_points.append(waypoint_coords)
        
        route_points.append(destination)
        
        # Smooth the route by removing unnecessary waypoints
        smoothed_route = self._smooth_route(route_points)
        
        print(f"Generated route with {len(smoothed_route)} waypoints")
        return smoothed_route
    
    def _create_direct_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Create a direct great circle route with minimal waypoints"""
        route_points = [origin]
        
        # Add 2-3 intermediate points for better visualization
        for i in range(1, 4):
            fraction = i / 4.0
            lat = origin[0] + (destination[0] - origin[0]) * fraction
            lng = origin[1] + (destination[1] - origin[1]) * fraction
            route_points.append((lat, lng))
        
        route_points.append(destination)
        return route_points
    
    def _create_fallback_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Create a fallback route when graph routing fails"""
        # Use a simple detour through open ocean
        mid_lat = (origin[0] + destination[0]) / 2
        mid_lng = (origin[1] + destination[1]) / 2
        
        # Move midpoint to open ocean (simplified)
        if mid_lng > 0:  # Eastern hemisphere
            mid_lng += 10  # Move east to open water
        else:  # Western hemisphere
            mid_lng -= 10  # Move west to open water
        
        return [origin, (mid_lat, mid_lng), destination]
    
    def _smooth_route(self, route_points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove unnecessary waypoints to smooth the route"""
        if len(route_points) <= 3:
            return route_points
        
        smoothed = [route_points[0]]  # Always keep origin
        
        i = 1
        while i < len(route_points) - 1:
            current = route_points[i]
            
            # Check if we can skip this waypoint by going directly to the next one
            can_skip = True
            if i + 1 < len(route_points):
                next_point = route_points[i + 1]
                if self.route_crosses_land(smoothed[-1], next_point):
                    can_skip = False
            
            if not can_skip:
                smoothed.append(current)
            
            i += 1
        
        smoothed.append(route_points[-1])  # Always keep destination
        return smoothed

# Global cities database with proper coordinates
GLOBAL_CITIES_DATABASE = {
    # Major Ports
    "Singapore": {"lat": 1.2966, "lng": 103.8006, "type": "port", "country": "Singapore"},
    "Rotterdam": {"lat": 51.9225, "lng": 4.4792, "type": "port", "country": "Netherlands"},
    "Shanghai": {"lat": 31.2304, "lng": 121.4737, "type": "port", "country": "China"},
    "Los Angeles": {"lat": 33.7361, "lng": -118.2639, "type": "port", "country": "USA"},
    "Hamburg": {"lat": 53.5405, "lng": 9.9759, "type": "port", "country": "Germany"},
    "Antwerp": {"lat": 51.2211, "lng": 4.4051, "type": "port", "country": "Belgium"},
    "Dubai": {"lat": 25.2582, "lng": 55.3341, "type": "port", "country": "UAE"},
    "Hong Kong": {"lat": 22.2793, "lng": 114.1628, "type": "port", "country": "Hong Kong"},
    
    # Major Cities - Americas
    "New York": {"lat": 40.7128, "lng": -74.0060, "type": "city", "country": "USA"},
    "Miami": {"lat": 25.7617, "lng": -80.1918, "type": "city", "country": "USA"},
    "San Francisco": {"lat": 37.7749, "lng": -122.4194, "type": "city", "country": "USA"},
    "Vancouver": {"lat": 49.2827, "lng": -123.1207, "type": "city", "country": "Canada"},
    "Toronto": {"lat": 43.6532, "lng": -79.3832, "type": "city", "country": "Canada"},
    "Mexico City": {"lat": 19.4326, "lng": -99.1332, "type": "city", "country": "Mexico"},
    "São Paulo": {"lat": -23.5505, "lng": -46.6333, "type": "city", "country": "Brazil"},
    "Rio de Janeiro": {"lat": -22.9068, "lng": -43.1729, "type": "city", "country": "Brazil"},
    "Buenos Aires": {"lat": -34.6118, "lng": -58.3960, "type": "city", "country": "Argentina"},
    
    # Major Cities - Europe
    "London": {"lat": 51.5074, "lng": -0.1278, "type": "city", "country": "UK"},
    "Paris": {"lat": 48.8566, "lng": 2.3522, "type": "city", "country": "France"},
    "Berlin": {"lat": 52.5200, "lng": 13.4050, "type": "city", "country": "Germany"},
    "Madrid": {"lat": 40.4168, "lng": -3.7038, "type": "city", "country": "Spain"},
    "Rome": {"lat": 41.9028, "lng": 12.4964, "type": "city", "country": "Italy"},
    "Amsterdam": {"lat": 52.3676, "lng": 4.9041, "type": "city", "country": "Netherlands"},
    "Stockholm": {"lat": 59.3293, "lng": 18.0686, "type": "city", "country": "Sweden"},
    "Copenhagen": {"lat": 55.6761, "lng": 12.5683, "type": "city", "country": "Denmark"},
    "Oslo": {"lat": 59.9139, "lng": 10.7522, "type": "city", "country": "Norway"},
    "Helsinki": {"lat": 60.1699, "lng": 24.9384, "type": "city", "country": "Finland"},
    
    # Major Cities - Asia
    "Tokyo": {"lat": 35.6762, "lng": 139.6503, "type": "city", "country": "Japan"},
    "Seoul": {"lat": 37.5665, "lng": 126.9780, "type": "city", "country": "South Korea"},
    "Beijing": {"lat": 39.9042, "lng": 116.4074, "type": "city", "country": "China"},
    "Mumbai": {"lat": 19.0760, "lng": 72.8777, "type": "city", "country": "India"},
    "Delhi": {"lat": 28.7041, "lng": 77.1025, "type": "city", "country": "India"},
    "Bangkok": {"lat": 13.7563, "lng": 100.5018, "type": "city", "country": "Thailand"},
    "Kuala Lumpur": {"lat": 3.1390, "lng": 101.6869, "type": "city", "country": "Malaysia"},
    "Jakarta": {"lat": -6.2088, "lng": 106.8456, "type": "city", "country": "Indonesia"},
    "Manila": {"lat": 14.5995, "lng": 120.9842, "type": "city", "country": "Philippines"},
    
    # Major Cities - Africa & Middle East
    "Cairo": {"lat": 30.0444, "lng": 31.2357, "type": "city", "country": "Egypt"},
    "Cape Town": {"lat": -33.9249, "lng": 18.4241, "type": "city", "country": "South Africa"},
    "Lagos": {"lat": 6.5244, "lng": 3.3792, "type": "city", "country": "Nigeria"},
    "Nairobi": {"lat": -1.2921, "lng": 36.8219, "type": "city", "country": "Kenya"},
    "Istanbul": {"lat": 41.0082, "lng": 28.9784, "type": "city", "country": "Turkey"},
    "Tehran": {"lat": 35.6892, "lng": 51.3890, "type": "city", "country": "Iran"},
    "Riyadh": {"lat": 24.7136, "lng": 46.6753, "type": "city", "country": "Saudi Arabia"},
    
    # Major Cities - Oceania
    "Sydney": {"lat": -33.8688, "lng": 151.2093, "type": "city", "country": "Australia"},
    "Melbourne": {"lat": -37.8136, "lng": 144.9631, "type": "city", "country": "Australia"},
    "Auckland": {"lat": -36.8485, "lng": 174.7633, "type": "city", "country": "New Zealand"},
}

# Global instance for the application
professional_router = ProfessionalMaritimeRouter()
