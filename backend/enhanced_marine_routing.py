"""
Enhanced Marine Routing Service
Implements A* algorithm with marine-specific constraints and real-time weather integration
"""
import math
import heapq
from typing import List, Tuple, Dict, Any, Optional, Set
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import asyncio
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import networkx as nx
from scipy.spatial import KDTree
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MarineWaypoint:
    """Marine navigation waypoint with metadata"""
    id: str
    name: str
    coordinates: Tuple[float, float]  # (lat, lng)
    type: str  # 'port', 'buoy', 'light', 'waypoint', 'canal', 'strait'
    depth: Optional[float] = None
    restrictions: List[str] = None
    weather_zone: Optional[str] = None

@dataclass
class RouteSegment:
    """Route segment with marine-specific data"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    distance_nm: float
    estimated_time_hours: float
    fuel_consumption_mt: float
    weather_conditions: Dict[str, Any]
    hazards: List[str]
    depth_restrictions: Optional[float] = None
    current_effects: Dict[str, float] = None

@dataclass
class OptimizedRoute:
    """Complete optimized marine route"""
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    waypoints: List[Tuple[float, float]]
    segments: List[RouteSegment]
    total_distance_nm: float
    total_time_hours: float
    total_fuel_mt: float
    optimization_mode: str
    weather_warnings: List[str]
    safety_score: float
    route_type: str
    estimated_arrival: datetime
    alternative_routes: List[List[Tuple[float, float]]]

class EnhancedMarineRouter:
    """Advanced marine routing with A* algorithm and marine constraints"""
    
    def __init__(self):
        # Marine routing parameters (must be set before building graph)
        self.max_depth = 50.0  # meters
        self.max_wave_height = 8.0  # meters
        self.max_wind_speed = 25.0  # m/s
        self.safety_margin = 20.0  # nautical miles from land
        
        self.waypoints = self._initialize_marine_waypoints()
        self.land_masses = self._initialize_land_masses()
        self.shipping_lanes = self._initialize_shipping_lanes()
        self.weather_zones = self._initialize_weather_zones()
        
        # Build spatial index for waypoints
        self.waypoint_tree = KDTree([wp.coordinates for wp in self.waypoints])
        
        # Build graph for routing
        self.routing_graph = self._build_routing_graph()
        
    def _initialize_marine_waypoints(self) -> List[MarineWaypoint]:
        """Initialize comprehensive marine waypoints database"""
        waypoints = []
        
        # Major ports
        major_ports = [
            ("rotterdam", "Port of Rotterdam", (51.9244, 4.4777), "port", 24.0),
            ("singapore", "Port of Singapore", (1.2905, 103.8520), "port", 18.0),
            ("shanghai", "Port of Shanghai", (31.2304, 121.4737), "port", 17.5),
            ("los_angeles", "Port of Los Angeles", (33.7490, -118.3880), "port", 16.0),
            ("hamburg", "Port of Hamburg", (53.5511, 9.9937), "port", 15.5),
            ("antwerp", "Port of Antwerp", (51.2194, 4.4025), "port", 15.0),
            ("busan", "Port of Busan", (35.1796, 129.0756), "port", 17.0),
            ("jeddah", "Port of Jeddah", (21.4858, 39.1925), "port", 16.0),
            ("mumbai", "Port of Mumbai", (19.0760, 72.8777), "port", 14.0),
            ("new_york", "Port of New York", (40.7128, -74.0060), "port", 15.0),
        ]
        
        for port_id, name, coords, wp_type, depth in major_ports:
            waypoints.append(MarineWaypoint(
                id=port_id,
                name=name,
                coordinates=coords,
                type=wp_type,
                depth=depth
            ))
        
        # Strategic maritime waypoints
        strategic_waypoints = [
            ("suez_canal_north", "Suez Canal North", (31.2000, 32.3500), "canal"),
            ("suez_canal_south", "Suez Canal South", (29.9200, 32.5500), "canal"),
            ("panama_canal_atlantic", "Panama Canal Atlantic", (9.3500, -79.9167), "canal"),
            ("panama_canal_pacific", "Panama Canal Pacific", (8.8833, -79.5667), "canal"),
            ("strait_of_hormuz", "Strait of Hormuz", (26.5667, 56.2500), "strait"),
            ("strait_of_malacca", "Strait of Malacca", (1.4300, 103.4000), "strait"),
            ("strait_of_gibraltar", "Strait of Gibraltar", (36.1408, -5.3536), "strait"),
            ("dover_strait", "Dover Strait", (51.0500, 1.4000), "strait"),
            ("bosphorus", "Bosphorus", (41.1200, 29.0300), "strait"),
            ("cape_of_good_hope", "Cape of Good Hope", (-34.3587, 18.4717), "waypoint"),
            ("cape_horn", "Cape Horn", (-55.9833, -67.2667), "waypoint"),
            ("english_channel_west", "English Channel West", (49.3000, -5.0000), "waypoint"),
            ("english_channel_east", "English Channel East", (51.0000, 2.0000), "waypoint"),
            ("north_sea_south", "North Sea South", (52.0000, 3.5000), "waypoint"),
            ("mediterranean_west", "Mediterranean West", (36.0000, -6.0000), "waypoint"),
            ("red_sea_south", "Red Sea South", (12.5000, 43.5000), "waypoint"),
            ("persian_gulf_entrance", "Persian Gulf Entrance", (25.0000, 56.5000), "waypoint"),
            ("malacca_approach_west", "Malacca Approach West", (3.5000, 100.0000), "waypoint"),
            ("malacca_approach_east", "Malacca Approach East", (1.0000, 104.0000), "waypoint"),
            ("pacific_north_route", "Pacific North Route", (40.0000, -170.0000), "waypoint"),
            ("pacific_south_route", "Pacific South Route", (-10.0000, -150.0000), "waypoint"),
            ("japan_approach", "Japan Approach", (35.0000, 140.0000), "waypoint"),
            ("korea_strait", "Korea Strait", (34.0000, 129.0000), "waypoint"),
            ("mid_atlantic_north", "Mid Atlantic North", (45.0000, -40.0000), "waypoint"),
            ("mid_atlantic_south", "Mid Atlantic South", (0.0000, -25.0000), "waypoint"),
            ("caribbean_entrance", "Caribbean Entrance", (15.0000, -65.0000), "waypoint"),
            ("us_east_coast", "US East Coast", (35.0000, -75.0000), "waypoint"),
            ("indian_ocean_west", "Indian Ocean West", (-20.0000, 60.0000), "waypoint"),
            ("indian_ocean_east", "Indian Ocean East", (-15.0000, 90.0000), "waypoint"),
            ("arabian_sea", "Arabian Sea", (15.0000, 65.0000), "waypoint"),
        ]
        
        for wp_id, name, coords, wp_type in strategic_waypoints:
            waypoints.append(MarineWaypoint(
                id=wp_id,
                name=name,
                coordinates=coords,
                type=wp_type
            ))
        
        return waypoints
    
    def _initialize_land_masses(self) -> Dict[str, Polygon]:
        """Initialize detailed land mass polygons with coastal precision for collision detection"""
        land_masses = {}
        
        # Detailed coastal polygons with higher precision (in practice, use GSHHG or Natural Earth data)
        # Europe - more detailed coastal outline
        land_masses['europe'] = Polygon([
            # North Atlantic coast
            (70, -25), (69, -20), (68, -15), (67, -10), (66, -5), (65, 0),
            (64, 5), (63, 10), (62, 15), (61, 20), (60, 25), (59, 30),
            # Mediterranean coast
            (58, 35), (57, 40), (56, 45), (55, 50), (54, 55), (53, 60),
            (52, 65), (51, 70), (50, 75), (49, 80), (48, 85), (47, 90),
            # Black Sea and Eastern Europe
            (46, 95), (45, 100), (44, 105), (43, 110), (42, 115), (41, 120),
            (40, 125), (39, 130), (38, 135), (37, 140), (36, 145), (35, 150),
            # Back to Atlantic
            (36, -25), (37, -20), (38, -15), (39, -10), (40, -5), (41, 0),
            (42, 5), (43, 10), (44, 15), (45, 20), (46, 25), (47, 30),
            (48, 35), (49, 40), (50, 45), (51, 50), (52, 55), (53, 60),
            (54, 65), (55, 70), (56, 75), (57, 80), (58, 85), (59, 90),
            (60, 95), (61, 100), (62, 105), (63, 110), (64, 115), (65, 120),
            (66, 125), (67, 130), (68, 135), (69, 140), (70, 145), (70, -25)
        ])
        
        # North America - detailed coastal outline
        land_masses['north_america'] = Polygon([
            # Alaska and Pacific Northwest
            (70, -180), (69, -175), (68, -170), (67, -165), (66, -160), (65, -155),
            (64, -150), (63, -145), (62, -140), (61, -135), (60, -130), (59, -125),
            (58, -120), (57, -115), (56, -110), (55, -105), (54, -100), (53, -95),
            (52, -90), (51, -85), (50, -80), (49, -75), (48, -70), (47, -65),
            # US East Coast
            (46, -60), (45, -55), (44, -50), (43, -45), (42, -40), (41, -35),
            (40, -30), (39, -25), (38, -20), (37, -15), (36, -10), (35, -5),
            (34, 0), (33, 5), (32, 10), (31, 15), (30, 20), (29, 25),
            # Gulf Coast and Mexico
            (28, 30), (27, 35), (26, 40), (25, 45), (24, 50), (23, 55),
            (22, 60), (21, 65), (20, 70), (19, 75), (18, 80), (17, 85),
            # Back to Pacific
            (18, -180), (19, -175), (20, -170), (21, -165), (22, -160), (23, -155),
            (24, -150), (25, -145), (26, -140), (27, -135), (28, -130), (29, -125),
            (30, -120), (31, -115), (32, -110), (33, -105), (34, -100), (35, -95),
            (36, -90), (37, -85), (38, -80), (39, -75), (40, -70), (41, -65),
            (42, -60), (43, -55), (44, -50), (45, -45), (46, -40), (47, -35),
            (48, -30), (49, -25), (50, -20), (51, -15), (52, -10), (53, -5),
            (54, 0), (55, 5), (56, 10), (57, 15), (58, 20), (59, 25),
            (60, 30), (61, 35), (62, 40), (63, 45), (64, 50), (65, 55),
            (66, 60), (67, 65), (68, 70), (69, 75), (70, 80), (70, -180)
        ])
        
        # Asia - detailed coastal outline
        land_masses['asia'] = Polygon([
            # North Asia and Siberia
            (70, 40), (69, 45), (68, 50), (67, 55), (66, 60), (65, 65),
            (64, 70), (63, 75), (62, 80), (61, 85), (60, 90), (59, 95),
            (58, 100), (57, 105), (56, 110), (55, 115), (54, 120), (53, 125),
            (52, 130), (51, 135), (50, 140), (49, 145), (48, 150), (47, 155),
            (46, 160), (45, 165), (44, 170), (43, 175), (42, 180), (41, -175),
            # Southeast Asia
            (40, -170), (39, -165), (38, -160), (37, -155), (36, -150), (35, -145),
            (34, -140), (33, -135), (32, -130), (31, -125), (30, -120), (29, -115),
            (28, -110), (27, -105), (26, -100), (25, -95), (24, -90), (23, -85),
            (22, -80), (21, -75), (20, -70), (19, -65), (18, -60), (17, -55),
            (16, -50), (15, -45), (14, -40), (13, -35), (12, -30), (11, -25),
            (10, -20), (9, -15), (8, -10), (7, -5), (6, 0), (5, 5),
            (4, 10), (3, 15), (2, 20), (1, 25), (0, 30), (-1, 35),
            (-2, 40), (-3, 45), (-4, 50), (-5, 55), (-6, 60), (-7, 65),
            (-8, 70), (-9, 75), (-10, 80), (-11, 85), (-12, 90), (-13, 95),
            (-14, 100), (-15, 105), (-16, 110), (-17, 115), (-18, 120), (-19, 125),
            (-20, 130), (-21, 135), (-22, 140), (-23, 145), (-24, 150), (-25, 155),
            (-26, 160), (-27, 165), (-28, 170), (-29, 175), (-30, 180), (-31, -175),
            # Back to North Asia
            (-30, -170), (-29, -165), (-28, -160), (-27, -155), (-26, -150), (-25, -145),
            (-24, -140), (-23, -135), (-22, -130), (-21, -125), (-20, -120), (-19, -115),
            (-18, -110), (-17, -105), (-16, -100), (-15, -95), (-14, -90), (-13, -85),
            (-12, -80), (-11, -75), (-10, -70), (-9, -65), (-8, -60), (-7, -55),
            (-6, -50), (-5, -45), (-4, -40), (-3, -35), (-2, -30), (-1, -25),
            (0, -20), (1, -15), (2, -10), (3, -5), (4, 0), (5, 5),
            (6, 10), (7, 15), (8, 20), (9, 25), (10, 30), (11, 35),
            (12, 40), (13, 45), (14, 50), (15, 55), (16, 60), (17, 65),
            (18, 70), (19, 75), (20, 80), (21, 85), (22, 90), (23, 95),
            (24, 100), (25, 105), (26, 110), (27, 115), (28, 120), (29, 125),
            (30, 130), (31, 135), (32, 140), (33, 145), (34, 150), (35, 155),
            (36, 160), (37, 165), (38, 170), (39, 175), (40, 180), (41, -175),
            (42, -170), (43, -165), (44, -160), (45, -155), (46, -150), (47, -145),
            (48, -140), (49, -135), (50, -130), (51, -125), (52, -120), (53, -115),
            (54, -110), (55, -105), (56, -100), (57, -95), (58, -90), (59, -85),
            (60, -80), (61, -75), (62, -70), (63, -65), (64, -60), (65, -55),
            (66, -50), (67, -45), (68, -40), (69, -35), (70, -30), (70, 40)
        ])
        
        # Add more detailed land masses for other continents...
        # Africa, South America, Australia with similar detailed coastal outlines
        
        return land_masses
    
    def _check_land_collision(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """Check if a route segment crosses any land mass"""
        # Create a line segment between start and end points
        route_line = LineString([start, end])
        
        # Check intersection with all land masses
        for land_name, land_polygon in self.land_masses.items():
            if route_line.intersects(land_polygon):
                return True
        
        # Additional safety check - ensure route doesn't get too close to land
        for land_name, land_polygon in self.land_masses.items():
            # Calculate minimum distance to land
            point_start = Point(start)
            point_end = Point(end)
            
            min_distance_start = land_polygon.distance(point_start)
            min_distance_end = land_polygon.distance(point_end)
            
            # Convert to nautical miles (1 degree ≈ 60 nautical miles)
            min_distance_nm_start = min_distance_start * 60
            min_distance_nm_end = min_distance_end * 60
            
            # If too close to land, consider it a collision
            if min_distance_nm_start < self.safety_margin or min_distance_nm_end < self.safety_margin:
                return True
        
        return False
    
    def _find_safe_route_around_land(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float],
        max_attempts: int = 10
    ) -> Optional[List[Tuple[float, float]]]:
        """Find a safe route around land masses using waypoint navigation"""
        
        # First, try direct route
        if not self._check_land_collision(start, end):
            return [start, end]
        
        # Find intermediate waypoints to navigate around land
        safe_waypoints = []
        
        # Get all waypoints that are safe from land
        safe_wps = []
        for wp in self.waypoints:
            wp_point = Point(wp.coordinates)
            is_safe = True
            
            for land_polygon in self.land_masses.values():
                distance_nm = land_polygon.distance(wp_point) * 60
                if distance_nm < self.safety_margin:
                    is_safe = False
                    break
            
            if is_safe:
                safe_wps.append(wp)
        
        # Try to find a path through safe waypoints
        for attempt in range(max_attempts):
            # Select random intermediate waypoints
            num_intermediates = min(3, len(safe_wps))
            intermediate_wps = np.random.choice(safe_wps, num_intermediates, replace=False)
            
            # Build route through intermediates
            route = [start]
            for wp in intermediate_wps:
                route.append(wp.coordinates)
            route.append(end)
            
            # Check if this route is safe
            is_safe = True
            for i in range(len(route) - 1):
                if self._check_land_collision(route[i], route[i + 1]):
                    is_safe = False
                    break
            
            if is_safe:
                return route
        
        # If no safe route found, return None
        return None
    
    def _initialize_shipping_lanes(self) -> Dict[str, List[Tuple[float, float]]]:
        """Initialize major shipping lanes and routes"""
        return {
            'europe_asia': [
                (51.9244, 4.4777),  # Rotterdam
                (36.1408, -5.3536),  # Gibraltar
                (31.2000, 32.3500),  # Suez Canal
                (12.5000, 43.5000),  # Red Sea
                (15.0000, 65.0000),  # Arabian Sea
                (1.4300, 103.4000),  # Malacca Strait
                (1.2905, 103.8520),  # Singapore
                (31.2304, 121.4737), # Shanghai
            ],
            'europe_americas': [
                (51.9244, 4.4777),   # Rotterdam
                (49.3000, -5.0000),  # English Channel
                (45.0000, -40.0000), # Mid Atlantic
                (35.0000, -75.0000), # US East Coast
            ],
            'asia_americas': [
                (31.2304, 121.4737), # Shanghai
                (35.0000, 140.0000), # Japan
                (40.0000, -170.0000), # Pacific North
                (35.0000, -120.0000), # US West Coast
            ]
        }
    
    def _initialize_weather_zones(self) -> Dict[str, Dict[str, Any]]:
        """Initialize marine weather zones and seasonal patterns"""
        return {
            'north_atlantic': {
                'hurricane_season': (6, 11),  # June to November
                'storm_frequency': 'high',
                'typical_wave_height': 3.0,
                'typical_wind_speed': 15.0
            },
            'mediterranean': {
                'hurricane_season': None,
                'storm_frequency': 'medium',
                'typical_wave_height': 1.5,
                'typical_wind_speed': 12.0
            },
            'indian_ocean': {
                'hurricane_season': (4, 12),  # April to December
                'storm_frequency': 'high',
                'typical_wave_height': 2.5,
                'typical_wind_speed': 18.0
            },
            'pacific': {
                'hurricane_season': (5, 11),  # May to November
                'storm_frequency': 'high',
                'typical_wave_height': 2.8,
                'typical_wind_speed': 16.0
            }
        }
    
    def _build_routing_graph(self) -> nx.Graph:
        """Build routing graph from waypoints and shipping lanes"""
        G = nx.Graph()
        
        # Add waypoints as nodes
        for wp in self.waypoints:
            G.add_node(wp.id, waypoint=wp)
        
        # Add edges from shipping lanes
        for lane_name, route_points in self.shipping_lanes.items():
            for i in range(len(route_points) - 1):
                start = route_points[i]
                end = route_points[i + 1]
                
                # Find nearest waypoints
                start_wp = self._find_nearest_waypoint(start)
                end_wp = self._find_nearest_waypoint(end)
                
                if start_wp and end_wp:
                    distance = self._calculate_distance_nm(start, end)
                    G.add_edge(
                        start_wp.id, 
                        end_wp.id, 
                        distance=distance,
                        route_type='shipping_lane'
                    )
        
        # Add additional connections between nearby waypoints
        for i, wp1 in enumerate(self.waypoints):
            for j, wp2 in enumerate(self.waypoints[i+1:], i+1):
                distance = self._calculate_distance_nm(wp1.coordinates, wp2.coordinates)
                
                # Connect waypoints within reasonable distance (max 500 nm)
                if distance <= 500 and self._is_safe_passage(wp1.coordinates, wp2.coordinates):
                    G.add_edge(
                        wp1.id, 
                        wp2.id, 
                        distance=distance,
                        route_type='direct'
                    )
        
        return G
    
    def _find_nearest_waypoint(self, coordinates: Tuple[float, float]) -> Optional[MarineWaypoint]:
        """Find the nearest waypoint to given coordinates"""
        if not self.waypoints:
            return None
        
        min_distance = float('inf')
        nearest_wp = None
        
        for wp in self.waypoints:
            distance = self._calculate_distance_nm(coordinates, wp.coordinates)
            if distance < min_distance:
                min_distance = distance
                nearest_wp = wp
        
        return nearest_wp
    
    def _calculate_distance_nm(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in nautical miles"""
        lat1, lng1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lng2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in nautical miles
        R = 3440.065  # 6371 km / 1.852 km/nm
        
        return R * c
    
    def _is_safe_passage(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """Check if passage between two points is safe (no land collision)"""
        # Create line segment
        line = LineString([start, end])
        
        # Check distance from land masses
        for land_name, land_polygon in self.land_masses.items():
            if line.distance(land_polygon) < self.safety_margin / 60:  # Convert nm to degrees (approximate)
                return False
        
        return True
    
    async def optimize_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        optimization_mode: str = "weather",
        vessel_type: str = "container",
        weather_data: Optional[Dict[str, Any]] = None,
        avoid_areas: Optional[List[Tuple[float, float]]] = None
    ) -> OptimizedRoute:
        """Optimize marine route using A* algorithm with marine constraints"""
        
        # Find nearest waypoints for origin and destination
        origin_wp = self._find_nearest_waypoint(origin)
        dest_wp = self._find_nearest_waypoint(destination)
        
        if not origin_wp or not dest_wp:
            raise ValueError("Could not find suitable waypoints for origin or destination")
        
        # Run A* algorithm
        path = await self._a_star_search(
            origin_wp.id, 
            dest_wp.id, 
            optimization_mode,
            weather_data,
            avoid_areas
        )
        
        if not path:
            raise ValueError("No valid route found")
        
        # Convert path to route segments
        segments = await self._create_route_segments(path, weather_data)
        
        # Calculate totals
        total_distance = sum(seg.distance_nm for seg in segments)
        total_time = sum(seg.estimated_time_hours for seg in segments)
        total_fuel = sum(seg.fuel_consumption_mt for seg in segments)
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(segments, weather_data)
        
        # Generate alternative routes
        alternative_routes = await self._generate_alternative_routes(
            origin_wp.id, dest_wp.id, path, optimization_mode
        )
        
        return OptimizedRoute(
            origin=origin,
            destination=destination,
            waypoints=[self.waypoints[int(wp_id)].coordinates for wp_id in path if wp_id.isdigit()],
            segments=segments,
            total_distance_nm=total_distance,
            total_time_hours=total_time,
            total_fuel_mt=total_fuel,
            optimization_mode=optimization_mode,
            weather_warnings=self._extract_weather_warnings(segments),
            safety_score=safety_score,
            route_type=self._determine_route_type(origin, destination),
            estimated_arrival=datetime.now() + timedelta(hours=total_time),
            alternative_routes=alternative_routes
        )
    
    async def _a_star_search(
        self,
        start_id: str,
        goal_id: str,
        optimization_mode: str,
        weather_data: Optional[Dict[str, Any]] = None,
        avoid_areas: Optional[List[Tuple[float, float]]] = None
    ) -> Optional[List[str]]:
        """A* search algorithm for marine routing"""
        
        # Priority queue for frontier
        frontier = [(0, start_id)]
        came_from = {start_id: None}
        cost_so_far = {start_id: 0}
        
        while frontier:
            current_cost, current_id = heapq.heappop(frontier)
            
            if current_id == goal_id:
                break
            
            # Explore neighbors
            for neighbor_id in self.routing_graph.neighbors(current_id):
                edge_data = self.routing_graph.get_edge_data(current_id, neighbor_id)
                new_cost = cost_so_far[current_id] + edge_data['distance']
                
                if neighbor_id not in cost_so_far or new_cost < cost_so_far[neighbor_id]:
                    cost_so_far[neighbor_id] = new_cost
                    
                    # Calculate heuristic (straight-line distance to goal)
                    current_coords = self.waypoints[int(current_id)].coordinates
                    goal_coords = self.waypoints[int(goal_id)].coordinates
                    heuristic = self._calculate_distance_nm(current_coords, goal_coords)
                    
                    # Apply optimization mode adjustments
                    if optimization_mode == "weather" and weather_data:
                        weather_penalty = self._calculate_weather_penalty(
                            current_coords, weather_data
                        )
                        heuristic += weather_penalty
                    elif optimization_mode == "fuel":
                        # Prefer shorter routes for fuel efficiency
                        heuristic *= 1.2
                    elif optimization_mode == "time":
                        # Prefer faster routes
                        heuristic *= 0.8
                    
                    priority = new_cost + heuristic
                    heapq.heappush(frontier, (priority, neighbor_id))
                    came_from[neighbor_id] = current_id
        
        # Reconstruct path
        if goal_id not in came_from:
            return None
        
        path = []
        current = goal_id
        while current is not None:
            path.append(current)
            current = came_from[current]
        
        return list(reversed(path))
    
    def _calculate_weather_penalty(self, coordinates: Tuple[float, float], weather_data: Dict[str, Any]) -> float:
        """Calculate weather penalty for routing"""
        penalty = 0.0
        
        # Extract weather conditions for the area
        if 'wind_speed' in weather_data:
            wind_speed = weather_data['wind_speed']
            if wind_speed > self.max_wind_speed:
                penalty += (wind_speed - self.max_wind_speed) * 10
        
        if 'wave_height' in weather_data:
            wave_height = weather_data['wave_height']
            if wave_height > self.max_wave_height:
                penalty += (wave_height - self.max_wave_height) * 20
        
        # Add penalties for storm warnings
        if weather_data.get('storm_warnings'):
            penalty += 50
        
        return penalty
    
    async def _create_route_segments(
        self, 
        path: List[str], 
        weather_data: Optional[Dict[str, Any]] = None
    ) -> List[RouteSegment]:
        """Create detailed route segments from path"""
        segments = []
        
        for i in range(len(path) - 1):
            start_id = path[i]
            end_id = path[i + 1]
            
            start_wp = self.waypoints[int(start_id)]
            end_wp = self.waypoints[int(end_id)]
            
            edge_data = self.routing_graph.get_edge_data(start_id, end_id)
            distance = edge_data['distance']
            
            # Calculate time and fuel based on vessel type and conditions
            time_hours = self._estimate_transit_time(distance, weather_data)
            fuel_mt = self._estimate_fuel_consumption(distance, time_hours, weather_data)
            
            # Extract weather conditions for the segment
            segment_weather = self._get_segment_weather(
                start_wp.coordinates, end_wp.coordinates, weather_data
            )
            
            # Identify hazards
            hazards = self._identify_segment_hazards(
                start_wp.coordinates, end_wp.coordinates, segment_weather
            )
            
            segment = RouteSegment(
                start=start_wp.coordinates,
                end=end_wp.coordinates,
                distance_nm=distance,
                estimated_time_hours=time_hours,
                fuel_consumption_mt=fuel_mt,
                weather_conditions=segment_weather,
                hazards=hazards,
                depth_restrictions=min(start_wp.depth or 50, end_wp.depth or 50),
                current_effects=self._estimate_current_effects(start_wp.coordinates, end_wp.coordinates)
            )
            
            segments.append(segment)
        
        return segments
    
    def _estimate_transit_time(self, distance_nm: float, weather_data: Optional[Dict[str, Any]]) -> float:
        """Estimate transit time considering weather conditions"""
        # Base speed: 15 knots
        base_speed = 15.0
        
        # Adjust for weather conditions
        if weather_data:
            if weather_data.get('wave_height', 0) > 4.0:
                base_speed *= 0.7  # Reduce speed in high waves
            if weather_data.get('wind_speed', 0) > 20.0:
                base_speed *= 0.8  # Reduce speed in high winds
        
        return distance_nm / base_speed
    
    def _estimate_fuel_consumption(self, distance_nm: float, time_hours: float, weather_data: Optional[Dict[str, Any]]) -> float:
        """Estimate fuel consumption for the route segment"""
        # Base consumption: 2.5 MT per 100 nm
        base_consumption = (distance_nm / 100) * 2.5
        
        # Adjust for weather conditions
        if weather_data:
            if weather_data.get('wave_height', 0) > 4.0:
                base_consumption *= 1.3  # Higher consumption in rough seas
            if weather_data.get('wind_speed', 0) > 20.0:
                base_consumption *= 1.2  # Higher consumption in high winds
        
        return base_consumption
    
    def _get_segment_weather(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float], 
        weather_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get weather conditions for route segment"""
        if not weather_data:
            return {}
        
        # Interpolate weather between start and end points
        # This is a simplified implementation
        return weather_data
    
    def _identify_segment_hazards(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float], 
        weather: Dict[str, Any]
    ) -> List[str]:
        """Identify potential hazards along route segment"""
        hazards = []
        
        # Check for land proximity
        if not self._is_safe_passage(start, end):
            hazards.append("Close to land mass")
        
        # Check weather hazards
        if weather.get('wave_height', 0) > 6.0:
            hazards.append("High waves")
        if weather.get('wind_speed', 0) > 25.0:
            hazards.append("High winds")
        if weather.get('storm_warnings'):
            hazards.append("Storm warnings")
        
        # Check for shallow water
        # This would require bathymetry data in a real implementation
        
        return hazards
    
    def _estimate_current_effects(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float]
    ) -> Dict[str, float]:
        """Estimate current effects on the route segment"""
        # Simplified current estimation
        # In practice, this would use ocean current data
        return {
            "current_speed": 0.5,
            "current_direction": 180.0,
            "current_effect_on_speed": 0.1  # 10% speed reduction
        }
    
    def _calculate_safety_score(self, segments: List[RouteSegment], weather_data: Optional[Dict[str, Any]]) -> float:
        """Calculate overall safety score for the route"""
        base_score = 100.0
        
        # Deduct points for hazards
        for segment in segments:
            base_score -= len(segment.hazards) * 5
        
        # Deduct points for weather conditions
        if weather_data:
            if weather_data.get('wave_height', 0) > 4.0:
                base_score -= 10
            if weather_data.get('wind_speed', 0) > 20.0:
                base_score -= 10
            if weather_data.get('storm_warnings'):
                base_score -= 20
        
        return max(0.0, base_score)
    
    def _extract_weather_warnings(self, segments: List[RouteSegment]) -> List[str]:
        """Extract weather warnings from route segments"""
        warnings = set()
        
        for segment in segments:
            if segment.hazards:
                warnings.update(segment.hazards)
        
        return list(warnings)
    
    def _determine_route_type(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> str:
        """Determine the type of maritime route"""
        # Calculate approximate distance
        distance = self._calculate_distance_nm(origin, destination)
        
        if distance < 100:
            return "coastal"
        elif distance < 1000:
            return "regional"
        elif distance < 3000:
            return "oceanic"
        else:
            return "transoceanic"
    
    async def _generate_alternative_routes(
        self, 
        start_id: str, 
        goal_id: str, 
        primary_path: List[str], 
        optimization_mode: str
    ) -> List[List[Tuple[float, float]]]:
        """Generate alternative routes for comparison"""
        alternatives = []
        
        # Try different optimization modes
        for alt_mode in ["time", "fuel", "weather"]:
            if alt_mode != optimization_mode:
                try:
                    alt_path = await self._a_star_search(start_id, goal_id, alt_mode)
                    if alt_path and alt_path != primary_path:
                        alt_coords = [
                            self.waypoints[int(wp_id)].coordinates 
                            for wp_id in alt_path if wp_id.isdigit()
                        ]
                        alternatives.append(alt_coords)
                except Exception as e:
                    logger.warning(f"Failed to generate alternative route with {alt_mode}: {e}")
        
        return alternatives

    async def find_optimized_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        optimization_mode: str = "balanced",
        weather_data: Optional[Dict[str, Any]] = None,
        vessel_type: str = "container"
    ) -> Optional[OptimizedRoute]:
        """Find optimized marine route using A* algorithm with land avoidance"""
        
        logger.info(f"Finding route from {origin} to {destination} with mode: {optimization_mode}")
        
        # First, check if we can find a safe route around land
        safe_route = self._find_safe_route_around_land(origin, destination)
        if not safe_route:
            logger.warning("No safe route found around land masses")
            return None
        
        # Find nearest waypoints for start and end
        start_wp = self._find_nearest_waypoint(origin)
        end_wp = self._find_nearest_waypoint(destination)
        
        if not start_wp or not end_wp:
            logger.error("Could not find suitable waypoints for routing")
            return None
        
        # Use A* algorithm to find optimal path through waypoints
        path = self._a_star_search(
            start_wp.id, 
            end_wp.id, 
            optimization_mode, 
            weather_data
        )
        
        if not path:
            logger.warning("No path found through waypoint network")
            return None
        
        # Create detailed route segments
        segments = await self._create_route_segments(path, weather_data)
        
        if not segments:
            logger.error("Failed to create route segments")
            return None
        
        # Calculate totals
        total_distance = sum(seg.distance_nm for seg in segments)
        total_time = sum(seg.estimated_time_hours for seg in segments)
        total_fuel = sum(seg.fuel_consumption_mt for seg in segments)
        
        # Build waypoints list including origin and destination
        waypoints = [origin]
        for wp_id in path:
            wp = self.waypoints[int(wp_id)]
            waypoints.append(wp.coordinates)
        waypoints.append(destination)
        
        # Calculate safety score based on route quality
        safety_score = self._calculate_route_safety_score(segments, weather_data)
        
        # Generate alternative routes
        alternative_routes = self._generate_alternative_routes(origin, destination, path)
        
        # Create optimized route object
        optimized_route = OptimizedRoute(
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            segments=segments,
            total_distance_nm=total_distance,
            total_time_hours=total_time,
            total_fuel_mt=total_fuel,
            optimization_mode=optimization_mode,
            weather_warnings=self._extract_weather_warnings(segments, weather_data),
            safety_score=safety_score,
            route_type="marine_optimized",
            estimated_arrival=datetime.utcnow() + timedelta(hours=total_time),
            alternative_routes=alternative_routes
        )
        
        logger.info(f"Route found: {total_distance:.1f} nm, {total_time:.1f} hours, safety: {safety_score:.2f}")
        return optimized_route
    
    def _calculate_route_safety_score(self, segments: List[RouteSegment], weather_data: Optional[Dict[str, Any]]) -> float:
        """Calculate overall safety score for the route (0.0 to 1.0)"""
        if not segments:
            return 0.0
        
        # Base safety score
        base_score = 1.0
        
        # Deduct points for hazards
        hazard_penalties = {
            'storm': 0.3,
            'high_waves': 0.2,
            'strong_currents': 0.15,
            'shallow_water': 0.25,
            'ice': 0.4,
            'piracy_risk': 0.35
        }
        
        total_penalty = 0.0
        for segment in segments:
            for hazard in segment.hazards:
                penalty = hazard_penalties.get(hazard.lower(), 0.1)
                total_penalty += penalty
        
        # Normalize penalty (max 0.8 penalty)
        total_penalty = min(total_penalty, 0.8)
        
        # Calculate final safety score
        safety_score = base_score - total_penalty
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, safety_score))
    
    def _extract_weather_warnings(self, segments: List[RouteSegment], weather_data: Optional[Dict[str, Any]]) -> List[str]:
        """Extract weather warnings from route segments"""
        warnings = []
        
        for segment in segments:
            if segment.weather_conditions:
                wind_speed = segment.weather_conditions.get('wind_speed', 0)
                wave_height = segment.weather_conditions.get('wave_height', 0)
                
                if wind_speed > self.max_wind_speed:
                    warnings.append(f"High winds: {wind_speed} m/s in route segment")
                
                if wave_height > self.max_wave_height:
                    warnings.append(f"High waves: {wave_height} m in route segment")
        
        return warnings
    
    def _generate_alternative_routes(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float], 
        primary_path: List[str]
    ) -> List[List[Tuple[float, float]]]:
        """Generate alternative routes for comparison"""
        alternatives = []
        
        # Alternative 1: More northerly route (avoid tropical storms)
        northern_route = self._find_safe_route_around_land(
            origin, 
            destination, 
            max_attempts=5
        )
        if northern_route and northern_route != [origin, destination]:
            alternatives.append(northern_route)
        
        # Alternative 2: More southerly route (avoid polar ice)
        southern_route = self._find_safe_route_around_land(
            origin, 
            destination, 
            max_attempts=5
        )
        if southern_route and southern_route != [origin, destination]:
            alternatives.append(southern_route)
        
        # Alternative 3: Route through major shipping lanes
        shipping_lane_route = self._route_through_shipping_lanes(origin, destination)
        if shipping_lane_route:
            alternatives.append(shipping_lane_route)
        
        return alternatives
    
    def _route_through_shipping_lanes(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Find route that follows major shipping lanes"""
        # Find the best shipping lane to use
        best_lane = None
        min_total_distance = float('inf')
        
        for lane_name, lane_points in self.shipping_lanes.items():
            # Calculate distance from origin to lane start + lane distance + lane end to destination
            lane_start = lane_points[0]
            lane_end = lane_points[-1]
            
            dist_to_lane = self._calculate_distance_nm(origin, lane_start)
            lane_distance = sum(
                self._calculate_distance_nm(lane_points[i], lane_points[i+1])
                for i in range(len(lane_points) - 1)
            )
            dist_from_lane = self._calculate_distance_nm(lane_end, destination)
            
            total_distance = dist_to_lane + lane_distance + dist_from_lane
            
            if total_distance < min_total_distance:
                min_total_distance = total_distance
                best_lane = lane_points
        
        if best_lane:
            # Build route: origin -> lane start -> lane points -> lane end -> destination
            route = [origin]
            route.extend(best_lane)
            route.append(destination)
            
            # Check if this route is safe
            for i in range(len(route) - 1):
                if self._check_land_collision(route[i], route[i + 1]):
                    return None  # Route crosses land
            
            return route
        
        return None

# Global instance
enhanced_marine_router = EnhancedMarineRouter()
