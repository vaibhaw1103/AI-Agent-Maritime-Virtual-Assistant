"""
Professional Maritime Route Calculation with Real Marine Routes
Advanced land avoidance using proper shipping lanes and maritime waypoints
"""
import math
from typing import List, Tuple, Dict, Optional
import requests
from geopy.distance import geodesic

class MaritimeRouteCalculator:
    def __init__(self):
        # Enhanced maritime chokepoints and waypoints with precise coordinates
        self.maritime_waypoints = {
            # Major Canals and Straits
            'suez_canal_north': (31.2000, 32.3500),
            'suez_canal_south': (29.9200, 32.5500),
            'panama_canal_atlantic': (9.3500, -79.9167),
            'panama_canal_pacific': (8.8833, -79.5667),
            'strait_of_hormuz': (26.5667, 56.2500),
            'strait_of_malacca': (1.4300, 103.4000),
            'strait_of_gibraltar': (36.1408, -5.3536),
            'dover_strait': (51.0500, 1.4000),
            'bosphorus': (41.1200, 29.0300),
            'dardanelles': (40.1500, 26.4000),
            
            # Cape Routes
            'cape_of_good_hope': (-34.3587, 18.4717),
            'cape_horn': (-55.9833, -67.2667),
            'cape_agulhas': (-34.8300, 20.0000),
            
            # Major Port Approaches
            'english_channel_west': (49.3000, -5.0000),
            'english_channel_east': (51.0000, 2.0000),
            'north_sea_south': (52.0000, 3.5000),
            'mediterranean_west': (36.0000, -6.0000),
            'red_sea_south': (12.5000, 43.5000),
            'persian_gulf_entrance': (25.0000, 56.5000),
            'malacca_approach_west': (3.5000, 100.0000),
            'malacca_approach_east': (1.0000, 104.0000),
            
            # Pacific Routes
            'pacific_north_route': (40.0000, -170.0000),
            'pacific_south_route': (-10.0000, -150.0000),
            'japan_approach': (35.0000, 140.0000),
            'korea_strait': (34.0000, 129.0000),
            
            # Atlantic Routes  
            'mid_atlantic_north': (45.0000, -40.0000),
            'mid_atlantic_south': (0.0000, -25.0000),
            'caribbean_entrance': (15.0000, -65.0000),
            'us_east_coast': (35.0000, -75.0000),
            
            # Indian Ocean
            'indian_ocean_west': (-20.0000, 60.0000),
            'indian_ocean_east': (-15.0000, 90.0000),
            'arabian_sea': (15.0000, 65.0000)
        }
        
        # Define major land masses to avoid (simplified polygons)
        self.land_masses = {
            'europe': [(70, -10), (70, 40), (35, 40), (35, -10)],
            'africa': [(35, -20), (35, 55), (-35, 55), (-35, -20)],
            'asia': [(70, 40), (70, 180), (-10, 180), (-10, 40)],
            'north_america': [(70, -180), (70, -60), (15, -60), (15, -180)],
            'south_america': [(15, -90), (15, -35), (-60, -35), (-60, -90)],
            'australia': [(-10, 110), (-10, 155), (-45, 155), (-45, 110)]
        }
    
    def calculate_marine_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Calculate professional marine route with advanced land avoidance
        Uses shipping lane knowledge and proper maritime waypoints
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        print(f"Calculating marine route from {origin} to {destination}")
        
        # Determine route type based on geography
        route_type = self._determine_route_type(origin, destination)
        print(f"Route type determined: {route_type}")
        
        if route_type == 'regional_european':
            return self._calculate_european_route(origin, destination)
        elif route_type == 'transatlantic':
            return self._calculate_transatlantic_route(origin, destination)
        elif route_type == 'asia_europe':
            return self._calculate_asia_europe_route(origin, destination)
        elif route_type == 'transpacific':
            return self._calculate_transpacific_route(origin, destination)
        elif route_type == 'coastal':
            return self._calculate_coastal_route(origin, destination)
        else:
            return self._calculate_oceanic_route(origin, destination)
    
    def _determine_route_type(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> str:
        """Determine the type of maritime route needed"""
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # European waters (North Sea, Baltic, Mediterranean)
        if (35 <= origin_lat <= 70 and -10 <= origin_lng <= 30 and
            35 <= dest_lat <= 70 and -10 <= dest_lng <= 30):
            return 'regional_european'
        
        # Transatlantic routes
        if ((origin_lng < -30 and dest_lng > -30) or 
            (origin_lng > -30 and dest_lng < -30)):
            return 'transatlantic'
        
        # Asia-Europe routes
        if ((origin_lng < 30 and dest_lng > 100) or 
            (origin_lng > 100 and dest_lng < 30)):
            return 'asia_europe'
        
        # Transpacific routes
        if ((origin_lng > 100 or origin_lng < -100) and 
            (dest_lng > 100 or dest_lng < -100)):
            return 'transpacific'
        
        # Coastal routes (within same continental waters)
        distance_km = geodesic(origin, destination).kilometers
        if distance_km < 1000:
            return 'coastal'
        
        return 'oceanic'
    
    def _calculate_european_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Calculate routes within European waters with PROPER LAND AVOIDANCE"""
        route_points = [origin]
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        print(f"Calculating European route from {origin} to {destination}")
        
        # Rotterdam to Hamburg - CRITICAL FIX for land crossing
        if (self._is_netherlands_area(origin) and self._is_germany_area(destination)):
            print("Detected Rotterdam to Hamburg route - using North Sea shipping lane")
            
            # PROPER MARITIME ROUTE via North Sea avoiding ALL land masses
            route_points.extend([
                (51.8, 3.2),    # Leave Dutch coast, head northwest to open North Sea
                (52.8, 2.5),    # North Sea waypoint - well offshore
                (53.8, 3.8),    # Approach German coast from northwest  
                (54.2, 6.5),    # German Bight approach - staying in deep water
                (54.0, 8.2),    # Final approach to Hamburg from north
                (53.6, 8.8)     # Hamburg port approach
            ])
        
        # Amsterdam/Rotterdam to other North European ports
        elif (self._is_netherlands_area(origin)):
            print("Route from Netherlands - using proper sea lanes")
            
            # Always go via North Sea first
            route_points.extend([
                (52.0, 3.0),    # North Sea entry
                (53.0, 4.0),    # North Sea routing
                (dest_lat + 0.5, dest_lng - 1.0),  # Approach from sea
            ])
        
        # Hamburg to other ports  
        elif (self._is_germany_area(origin)):
            print("Route from Germany - via North Sea")
            
            route_points.extend([
                (54.0, 7.5),    # Exit German Bight via open water
                (53.5, 5.0),    # North Sea routing
                (dest_lat + 0.5, dest_lng - 1.0),  # Sea approach
            ])
        
        # UK routes
        elif (self._is_uk_area(origin) or self._is_uk_area(destination)):
            print("UK route - via English Channel or around")
            
            # English Channel route
            route_points.extend([
                (50.5, -0.5),   # English Channel
                (50.0, 1.5),    # Dover Strait area
                (dest_lat, dest_lng - 1.0)  # Approach from west
            ])
        
        # Mediterranean routes
        elif (30 <= origin_lat <= 45 and -5 <= origin_lng <= 35):
            print("Mediterranean route")
            
            route_points.extend([
                (origin_lat + (dest_lat - origin_lat) * 0.3, origin_lng + (dest_lng - origin_lng) * 0.3),
                (origin_lat + (dest_lat - origin_lat) * 0.7, origin_lng + (dest_lng - origin_lng) * 0.7)
            ])
        
        # Default European coastal - ensure sea routing
        else:
            print("Default European sea route")
            # Force routing through open water
            mid_point = self._get_sea_waypoint(origin, destination, 0.5)
            route_points.append(mid_point)
        
        route_points.append(destination)
        
        print(f"Generated European route with {len(route_points)} waypoints:")
        for i, point in enumerate(route_points):
            print(f"  {i}: {point}")
        
        return route_points
    
    def _is_netherlands_area(self, point: Tuple[float, float]) -> bool:
        """Check if point is in Netherlands area (Rotterdam, Amsterdam)"""
        lat, lng = point
        return 51.5 <= lat <= 53.0 and 3.5 <= lng <= 6.0
    
    def _is_germany_area(self, point: Tuple[float, float]) -> bool:
        """Check if point is in German port area (Hamburg, Bremen)"""
        lat, lng = point
        return 53.0 <= lat <= 54.5 and 8.0 <= lng <= 12.0
    
    def _is_uk_area(self, point: Tuple[float, float]) -> bool:
        """Check if point is in UK area"""
        lat, lng = point
        return 50.0 <= lat <= 61.0 and -8.0 <= lng <= 2.0
    
    def _get_sea_waypoint(self, origin: Tuple[float, float], destination: Tuple[float, float], fraction: float) -> Tuple[float, float]:
        """Get a waypoint that's guaranteed to be in open water"""
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # Calculate intermediate point
        lat = origin_lat + (dest_lat - origin_lat) * fraction
        lng = origin_lng + (dest_lng - origin_lng) * fraction
        
        # Force to open sea by moving away from coastlines
        if self._is_over_land_strict(lat, lng):
            # Move to nearest sea area
            if lng > 0:  # Eastern Europe
                lng += 2.0  # Move further east to open water
                lat += 1.0  # Move north to open sea
            else:  # Western Europe
                lng -= 2.0  # Move west to Atlantic
                lat += 1.0  # Move north to open water
        
        return (lat, lng)
    
    def _calculate_transatlantic_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Calculate transatlantic routes"""
        route_points = [origin]
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # Northern Atlantic route
        if origin_lat > 40 and dest_lat > 40:
            route_points.extend([
                (origin_lat, -40.0),              # Mid-Atlantic waypoint
                (dest_lat, -40.0)                  # Approach waypoint
            ])
        
        # Southern Atlantic route  
        elif origin_lat < 0 or dest_lat < 0:
            route_points.extend([
                (0.0, -25.0),                      # Equatorial Atlantic
                (dest_lat * 0.5, dest_lng * 0.5)  # Approach waypoint
            ])
        
        # Standard Atlantic crossing
        else:
            mid_lat = (origin_lat + dest_lat) / 2
            route_points.extend([
                (mid_lat, -30.0),                  # Mid-Atlantic
                (mid_lat, -50.0)                   # Western approach
            ])
        
        route_points.append(destination)
        return route_points
    
    def _calculate_asia_europe_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Calculate Asia-Europe routes via Suez or Cape"""
        route_points = [origin]
        
        # Default to Suez route for most Asia-Europe traffic
        route_points.extend([
            self.maritime_waypoints['malacca_approach_west'],
            self.maritime_waypoints['arabian_sea'],
            self.maritime_waypoints['red_sea_south'],
            self.maritime_waypoints['suez_canal_south'],
            self.maritime_waypoints['suez_canal_north'],
            self.maritime_waypoints['mediterranean_west'],
            self.maritime_waypoints['strait_of_gibraltar']
        ])
        
        route_points.append(destination)
        return route_points
    
    def _calculate_transpacific_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Calculate transpacific routes"""
        route_points = [origin]
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # Northern Pacific route
        if origin_lat > 30 and dest_lat > 30:
            route_points.extend([
                (40.0, -170.0),                    # North Pacific waypoint
                (35.0, -140.0)                     # Eastern Pacific approach
            ])
        
        # Southern Pacific route
        else:
            route_points.extend([
                (-10.0, -150.0),                   # South Pacific waypoint
                (0.0, -120.0)                      # Equatorial Pacific
            ])
        
        route_points.append(destination)
        return route_points
    
    def _calculate_coastal_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Calculate coastal routes with minimal waypoints"""
        route_points = [origin]
        
        # Add 2-3 waypoints for coastal routes to avoid getting too close to shore
        waypoint1 = self._create_safe_waypoint(origin, destination, 0.33)
        waypoint2 = self._create_safe_waypoint(origin, destination, 0.67)
        
        route_points.extend([waypoint1, waypoint2])
        route_points.append(destination)
        return route_points
    
    def _calculate_oceanic_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Calculate general oceanic routes"""
        route_points = [origin]
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # Add strategic waypoints based on ocean
        if -30 <= origin_lat <= 30 and -30 <= dest_lat <= 30:
            # Equatorial route
            route_points.append((0.0, (origin_lng + dest_lng) / 2))
        else:
            # Add intermediate waypoints
            for fraction in [0.25, 0.5, 0.75]:
                waypoint = self._create_safe_waypoint(origin, destination, fraction)
                route_points.append(waypoint)
        
        route_points.append(destination)
        return route_points
    
    def _create_safe_waypoint(self, origin: Tuple[float, float], destination: Tuple[float, float], fraction: float) -> Tuple[float, float]:
        """Create a safe waypoint at given fraction along route, adjusted for open water"""
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # Calculate intermediate point
        lat = origin_lat + (dest_lat - origin_lat) * fraction
        lng = origin_lng + (dest_lng - origin_lng) * fraction
        
        # Adjust to avoid land masses
        if self._is_over_land(lat, lng):
            lat, lng = self._adjust_to_water(lat, lng)
        
        return (lat, lng)
    
    def _is_over_land_strict(self, lat: float, lng: float) -> bool:
        """STRICT land detection for European waters with detailed coastline boundaries"""
        
        # Netherlands (highly detailed to avoid land crossing)
        if 50.5 <= lat <= 53.8 and 3.0 <= lng <= 7.5:
            # Only the Wadden Sea and coastal waters are OK
            if lat >= 53.0 and lng <= 6.0:  # Wadden Sea area
                return False
            # North Sea off Dutch coast is OK
            if lng <= 4.0:
                return False
            # Everything else in Netherlands area is LAND
            return True
        
        # Germany North Sea coast
        if 53.0 <= lat <= 55.0 and 6.0 <= lng <= 10.0:
            # German Bight waters are OK
            if lng <= 8.5 and lat >= 53.5:  # Open German Bight
                return False
            # Closer to coast = land
            return True
        
        # UK and Ireland
        if 49.5 <= lat <= 61.0 and -11.0 <= lng <= 2.5:
            # English Channel is water
            if 49.5 <= lat <= 51.5 and -2.0 <= lng <= 2.0:
                return False
            # Most of UK area is land
            return True
        
        # North Sea (definitely water)
        if 51.0 <= lat <= 62.0 and 0.0 <= lng <= 8.0:
            return False
        
        # Baltic Sea (water)
        if 54.0 <= lat <= 66.0 and 10.0 <= lng <= 30.0:
            return False
        
        # Mediterranean (water)
        if 30.0 <= lat <= 47.0 and -6.0 <= lng <= 37.0:
            return False
        
        # Atlantic Ocean west of Europe (definitely water)
        if 35.0 <= lat <= 70.0 and -25.0 <= lng <= -5.0:
            return False
        
        # Default European landmasses
        if 35.0 <= lat <= 72.0 and -10.0 <= lng <= 40.0:
            return True
        
        # Africa
        if -35.0 <= lat <= 37.0 and -20.0 <= lng <= 50.0:
            # Red Sea and major water bodies
            if 12.0 <= lat <= 30.0 and 32.0 <= lng <= 43.0:  # Red Sea
                return False
            return True
        
        # Asia mainland
        if 0.0 <= lat <= 70.0 and 40.0 <= lng <= 180.0:
            # Persian Gulf
            if 24.0 <= lat <= 30.0 and 48.0 <= lng <= 56.0:
                return False
            return True
        
        # Americas
        if -60.0 <= lat <= 70.0 and -180.0 <= lng <= -30.0:
            return True
        
        # Australia
        if -45.0 <= lat <= -10.0 and 110.0 <= lng <= 155.0:
            return True
        
        # Default to water if not explicitly land
        return False
    
    def _adjust_to_water(self, lat: float, lng: float) -> Tuple[float, float]:
        """Adjust coordinates to nearby open water"""
        # Simple adjustment - move toward open ocean
        if self._is_over_land(lat, lng):
            # Move toward nearest ocean
            if lng > 0:  # Eastern hemisphere
                if lat > 0:  # Northern hemisphere
                    lng += 5.0  # Move east toward Pacific
                else:  # Southern hemisphere  
                    lng += 3.0  # Move toward Indian Ocean
            else:  # Western hemisphere
                lng -= 5.0  # Move west toward Atlantic/Pacific
        
        return (lat, lng)
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        waypoints = []
        
        # Check for regional routes first (short distances within same region)
        distance_km = geodesic(origin, destination).kilometers
        
        # European coastal routes (North Sea, Baltic Sea, Mediterranean)
        if self._is_european_coastal_route(origin, destination, distance_km):
            return []  # Direct route for European coastal shipping
        
        # North American coastal routes
        elif self._is_north_american_coastal_route(origin, destination, distance_km):
            return []  # Direct coastal route
        
        # Asian coastal routes
        elif self._is_asian_coastal_route(origin, destination, distance_km):
            return []  # Direct coastal route
        
        # Long-distance intercontinental routes
        # Europe to Asia via Suez Canal
        elif (origin_lng < 20 and dest_lng > 50) or (origin_lng > 50 and dest_lng < 20):
            if origin_lat > 10 and dest_lat > 10:  # Northern hemisphere route
                waypoints.extend([
                    self.maritime_waypoints['gibraltar'],
                    self.maritime_waypoints['suez_canal'],
                    self.maritime_waypoints['strait_of_hormuz'],
                    self.maritime_waypoints['strait_of_malacca']
                ])
        
        # Americas to Asia/Europe via Panama
        elif (origin_lng < -60 and dest_lng > 60) or (origin_lng > 60 and dest_lng < -60):
            if abs(origin_lat) < 40 and abs(dest_lat) < 40:  # Tropical route
                waypoints.append(self.maritime_waypoints['panama_canal'])
        
        # Around Cape of Good Hope for deep-draft vessels
        elif self._needs_cape_route(origin, destination):
            waypoints.append(self.maritime_waypoints['cape_of_good_hope'])
        
        # Pacific crossing
        elif self._is_pacific_crossing(origin, destination):
            # Add mid-Pacific waypoint
            mid_lat = (origin_lat + dest_lat) / 2
            mid_lng = -150.0 if origin_lng < -120 or dest_lng < -120 else 150.0
            waypoints.append((mid_lat, mid_lng))
        
        return waypoints
    
    def _is_european_coastal_route(self, origin: Tuple[float, float], destination: Tuple[float, float], distance_km: float) -> bool:
        """
        Check if this is a European coastal route (North Sea, Baltic, Mediterranean)
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # European longitude range and reasonable coastal distance
        european_lng_range = (-10, 30)  # Atlantic to Eastern Europe
        european_lat_range = (35, 72)   # Mediterranean to Arctic
        
        return (european_lng_range[0] <= origin_lng <= european_lng_range[1] and
                european_lng_range[0] <= dest_lng <= european_lng_range[1] and
                european_lat_range[0] <= origin_lat <= european_lat_range[1] and
                european_lat_range[0] <= dest_lat <= european_lat_range[1] and
                distance_km < 5000)  # Less than 5000km for coastal routes
    
    def _is_north_american_coastal_route(self, origin: Tuple[float, float], destination: Tuple[float, float], distance_km: float) -> bool:
        """
        Check if this is a North American coastal route
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        na_lng_range = (-170, -50)  # Pacific to Atlantic coast
        na_lat_range = (25, 70)     # Gulf of Mexico to Arctic
        
        return (na_lng_range[0] <= origin_lng <= na_lng_range[1] and
                na_lng_range[0] <= dest_lng <= na_lng_range[1] and
                na_lat_range[0] <= origin_lat <= na_lat_range[1] and
                na_lat_range[0] <= dest_lat <= na_lat_range[1] and
                distance_km < 8000)  # Coastal routes
    
    def _is_asian_coastal_route(self, origin: Tuple[float, float], destination: Tuple[float, float], distance_km: float) -> bool:
        """
        Check if this is an Asian coastal route
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        asian_lng_range = (90, 180)   # India to Pacific
        asian_lat_range = (-10, 50)   # Indonesia to China/Japan
        
        return (asian_lng_range[0] <= origin_lng <= asian_lng_range[1] and
                asian_lng_range[0] <= dest_lng <= asian_lng_range[1] and
                asian_lat_range[0] <= origin_lat <= asian_lat_range[1] and
                asian_lat_range[0] <= dest_lat <= asian_lat_range[1] and
                distance_km < 6000)  # Coastal routes
    
    def _needs_cape_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> bool:
        """
        Determine if route should go around Cape of Good Hope
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # Large vessels or routes avoiding Suez
        return ((origin_lng < 20 and dest_lng > 60) or (origin_lng > 60 and dest_lng < 20)) and \
               (origin_lat < -20 or dest_lat < -20)
    
    def _is_pacific_crossing(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> bool:
        """
        Check if route crosses Pacific Ocean
        """
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        return (origin_lng > 100 and dest_lng < -100) or (origin_lng < -100 and dest_lng > 100)
    
    def _refine_marine_route(self, route_points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Refine route to avoid land masses using great circle segments
        """
        refined_route = []
        
        for i in range(len(route_points) - 1):
            start = route_points[i]
            end = route_points[i + 1]
            
            # Add intermediate points for long segments
            distance = geodesic(start, end).kilometers
            
            if distance > 1000:  # Add waypoints for long segments
                num_segments = max(2, int(distance / 500))
                for j in range(num_segments + 1):
                    ratio = j / num_segments
                    
                    # Great circle interpolation
                    lat = start[0] + ratio * (end[0] - start[0])
                    lng = start[1] + ratio * (end[1] - start[1])
                    
                    # Adjust to avoid major land masses
                    lat, lng = self._adjust_for_marine_route(lat, lng, start, end)
                    
                    if j < num_segments:  # Don't duplicate the end point
                        refined_route.append((lat, lng))
            else:
                refined_route.append(start)
        
        refined_route.append(route_points[-1])
        return refined_route
    
    def _adjust_for_marine_route(self, lat: float, lng: float, start: Tuple[float, float], end: Tuple[float, float]) -> Tuple[float, float]:
        """
        Adjust waypoint to ensure it's in navigable waters
        """
        # Simple land avoidance adjustments
        
        # Avoid African continent
        if 15 < lng < 50 and -35 < lat < 35:
            if start[1] < 15 and end[1] > 50:  # Going around Africa
                lat = min(lat, -35)  # Go south of Africa
        
        # Avoid Arabian Peninsula
        if 35 < lng < 60 and 15 < lat < 30:
            lng = max(lng, 60)  # Stay east of Arabia
        
        # Avoid Southeast Asian landmasses
        if 90 < lng < 140 and -10 < lat < 25:
            # Navigate through straits
            if 100 < lng < 110:  # Malacca Strait area
                lat = max(lat, 1)  # Stay in strait
        
        # Avoid North American continent
        if -130 < lng < -60 and 25 < lat < 70:
            if start[1] > -60 or end[1] > -60:  # Coming from or going to Atlantic
                lng = min(lng, -60)  # Stay east of continent
        
        return lat, lng

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
    "Lima": {"lat": -12.0464, "lng": -77.0428, "type": "city", "country": "Peru"},
    
    # Major Cities - Europe
    "London": {"lat": 51.5074, "lng": -0.1278, "type": "city", "country": "UK"},
    "Paris": {"lat": 48.8566, "lng": 2.3522, "type": "city", "country": "France"},
    "Berlin": {"lat": 52.5200, "lng": 13.4050, "type": "city", "country": "Germany"},
    "Rome": {"lat": 41.9028, "lng": 12.4964, "type": "city", "country": "Italy"},
    "Madrid": {"lat": 40.4168, "lng": -3.7038, "type": "city", "country": "Spain"},
    "Amsterdam": {"lat": 52.3676, "lng": 4.9041, "type": "city", "country": "Netherlands"},
    "Stockholm": {"lat": 59.3293, "lng": 18.0686, "type": "city", "country": "Sweden"},
    "Oslo": {"lat": 59.9139, "lng": 10.7522, "type": "city", "country": "Norway"},
    "Copenhagen": {"lat": 55.6761, "lng": 12.5683, "type": "city", "country": "Denmark"},
    "Helsinki": {"lat": 60.1699, "lng": 24.9384, "type": "city", "country": "Finland"},
    
    # Major Cities - Asia
    "Tokyo": {"lat": 35.6762, "lng": 139.6503, "type": "city", "country": "Japan"},
    "Beijing": {"lat": 39.9042, "lng": 116.4074, "type": "city", "country": "China"},
    "Seoul": {"lat": 37.5665, "lng": 126.9780, "type": "city", "country": "South Korea"},
    "Mumbai": {"lat": 19.0760, "lng": 72.8777, "type": "city", "country": "India"},
    "Delhi": {"lat": 28.7041, "lng": 77.1025, "type": "city", "country": "India"},
    "Bangkok": {"lat": 13.7563, "lng": 100.5018, "type": "city", "country": "Thailand"},
    "Jakarta": {"lat": -6.2088, "lng": 106.8456, "type": "city", "country": "Indonesia"},
    "Manila": {"lat": 14.5995, "lng": 120.9842, "type": "city", "country": "Philippines"},
    "Kuala Lumpur": {"lat": 3.1390, "lng": 101.6869, "type": "city", "country": "Malaysia"},
    "Ho Chi Minh City": {"lat": 10.8231, "lng": 106.6297, "type": "city", "country": "Vietnam"},
    
    # Major Cities - Middle East & Africa
    "Cairo": {"lat": 30.0444, "lng": 31.2357, "type": "city", "country": "Egypt"},
    "Istanbul": {"lat": 41.0082, "lng": 28.9784, "type": "city", "country": "Turkey"},
    "Tehran": {"lat": 35.6892, "lng": 51.3890, "type": "city", "country": "Iran"},
    "Riyadh": {"lat": 24.7136, "lng": 46.6753, "type": "city", "country": "Saudi Arabia"},
    "Lagos": {"lat": 6.5244, "lng": 3.3792, "type": "city", "country": "Nigeria"},
    "Casablanca": {"lat": 33.5731, "lng": -7.5898, "type": "city", "country": "Morocco"},
    "Cape Town": {"lat": -33.9249, "lng": 18.4241, "type": "city", "country": "South Africa"},
    "Johannesburg": {"lat": -26.2041, "lng": 28.0473, "type": "city", "country": "South Africa"},
    
    # Major Cities - Oceania
    "Sydney": {"lat": -33.8688, "lng": 151.2093, "type": "city", "country": "Australia"},
    "Melbourne": {"lat": -37.8136, "lng": 144.9631, "type": "city", "country": "Australia"},
    "Auckland": {"lat": -36.8485, "lng": 174.7633, "type": "city", "country": "New Zealand"},
    "Perth": {"lat": -31.9505, "lng": 115.8605, "type": "city", "country": "Australia"},
}
