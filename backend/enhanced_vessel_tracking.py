"""
Enhanced Vessel Tracking Service
Provides real-time vessel tracking with IMO/MMSI resolution and position history
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import json
import re
import math

logger = logging.getLogger(__name__)

@dataclass
class VesselPosition:
    """Vessel position with timestamp and metadata"""
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float  # knots
    heading: float  # degrees
    course: float  # degrees
    status: str
    source: str

@dataclass
class VesselDetails:
    """Comprehensive vessel information"""
    imo: str
    mmsi: str
    name: str
    callsign: str
    vessel_type: str
    flag: str
    gross_tonnage: Optional[int] = None
    length: Optional[float] = None
    width: Optional[float] = None
    draft: Optional[float] = None
    year_built: Optional[int] = None
    home_port: Optional[str] = None
    operator: Optional[str] = None
    last_updated: Optional[datetime] = None

@dataclass
class VesselTrack:
    """Complete vessel tracking information"""
    vessel: VesselDetails
    current_position: VesselPosition
    position_history: List[VesselPosition]
    destination: Optional[str] = None
    eta: Optional[datetime] = None
    route_points: List[Tuple[float, float]] = None
    weather_conditions: Dict[str, Any] = None
    alerts: List[str] = None

class EnhancedVesselTracker:
    """Advanced vessel tracking with multiple API integrations"""
    
    def __init__(self):
        self.marinetraffic_api_key = os.getenv("MARINETRAFFIC_API_KEY")
        self.vesselfinder_api_key = os.getenv("VESSELFINDER_API_KEY")
        self.shipfinder_api_key = os.getenv("SHIPFINDER_API_KEY")
        self.ais_api_key = os.getenv("AIS_API_KEY")
        
        # API endpoints
        self.marinetraffic_base = "https://services.marinetraffic.com/api"
        self.vesselfinder_base = "https://api.vesselfinder.com"
        self.shipfinder_base = "https://api.shipfinder.com"
        self.ais_base = "https://api.ais.com"
        
        # Vessel cache
        self.vessel_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Mock vessel database for development
        self.mock_vessels = self._initialize_mock_vessels()
    
    def _initialize_mock_vessels(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock vessel database for development/testing"""
        return {
            "9123456": {  # IMO
                "imo": "9123456",
                "mmsi": "123456789",
                "name": "MARITIME STAR",
                "callsign": "ABCD",
                "vessel_type": "Container Ship",
                "flag": "Panama",
                "gross_tonnage": 45000,
                "length": 300.0,
                "width": 40.0,
                "draft": 14.5,
                "year_built": 2015,
                "home_port": "Rotterdam",
                "operator": "Maersk Line"
            },
            "9876543": {  # IMO
                "imo": "9876543",
                "mmsi": "987654321",
                "name": "OCEAN VOYAGER",
                "callsign": "EFGH",
                "vessel_type": "Bulk Carrier",
                "flag": "Liberia",
                "gross_tonnage": 82000,
                "length": 280.0,
                "width": 45.0,
                "draft": 16.0,
                "year_built": 2018,
                "home_port": "Singapore",
                "operator": "COSCO Shipping"
            },
            "123456789": {  # MMSI
                "imo": "9123456",
                "mmsi": "123456789",
                "name": "MARITIME STAR",
                "callsign": "ABCD",
                "vessel_type": "Container Ship",
                "flag": "Panama",
                "gross_tonnage": 45000,
                "length": 300.0,
                "width": 40.0,
                "draft": 14.5,
                "year_built": 2015,
                "home_port": "Rotterdam",
                "operator": "Maersk Line"
            }
        }
    
    async def track_vessel(
        self, 
        identifier: str, 
        include_history: bool = True,
        history_hours: int = 24
    ) -> Optional[VesselTrack]:
        """Track vessel by IMO, MMSI, or name"""
        try:
            # Normalize identifier
            identifier = identifier.strip().upper()
            
            # Determine identifier type
            identifier_type = self._identify_identifier_type(identifier)
            
            # Try to get vessel details
            vessel_details = await self._get_vessel_details(identifier, identifier_type)
            if not vessel_details:
                return None
            
            # Get current position
            current_position = await self._get_vessel_position(vessel_details)
            if not current_position:
                return None
            
            # Get position history if requested
            position_history = []
            if include_history:
                position_history = await self._get_position_history(
                    vessel_details, history_hours
                )
            
            # Get destination and ETA
            destination, eta = await self._get_vessel_destination(vessel_details)
            
            # Get route points
            route_points = await self._get_vessel_route(vessel_details)
            
            # Get weather conditions
            weather_conditions = await self._get_vessel_weather(current_position)
            
            # Generate alerts
            alerts = self._generate_vessel_alerts(vessel_details, current_position, weather_conditions)
            
            return VesselTrack(
                vessel=vessel_details,
                current_position=current_position,
                position_history=position_history,
                destination=destination,
                eta=eta,
                route_points=route_points,
                weather_conditions=weather_conditions,
                alerts=alerts
            )
            
        except Exception as e:
            logger.error(f"Vessel tracking failed for {identifier}: {e}")
            return None
    
    async def search_vessels(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[VesselDetails]:
        """Search for vessels by name, IMO, MMSI, or callsign"""
        try:
            query = query.strip().upper()
            results = []
            
            # Search in mock database
            for vessel_id, vessel_data in self.mock_vessels.items():
                if (query in vessel_data['name'].upper() or
                    query in vessel_data['imo'] or
                    query in vessel_data['mmsi'] or
                    query in vessel_data['callsign']):
                    results.append(VesselDetails(**vessel_data))
                    
                    if len(results) >= limit:
                        break
            
            # Try real APIs if available
            if self.marinetraffic_api_key:
                try:
                    api_results = await self._search_marinetraffic(query, limit)
                    results.extend(api_results)
                except Exception as e:
                    logger.warning(f"MarineTraffic search failed: {e}")
            
            # Remove duplicates and limit results
            unique_results = self._deduplicate_vessels(results)
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Vessel search failed: {e}")
            return []
    
    def _identify_identifier_type(self, identifier: str) -> str:
        """Identify the type of vessel identifier"""
        # IMO: 7 digits
        if re.match(r'^\d{7}$', identifier):
            return 'imo'
        
        # MMSI: 9 digits
        if re.match(r'^\d{9}$', identifier):
            return 'mmsi'
        
        # Callsign: 4-6 alphanumeric characters
        if re.match(r'^[A-Z0-9]{4,6}$', identifier):
            return 'callsign'
        
        # Name: anything else
        return 'name'
    
    async def _get_vessel_details(
        self, 
        identifier: str, 
        identifier_type: str
    ) -> Optional[VesselDetails]:
        """Get vessel details from various sources"""
        
        # Check cache first
        cache_key = f"{identifier_type}_{identifier}"
        if cache_key in self.vessel_cache:
            cached_data = self.vessel_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
        
        # Try mock database first
        if identifier_type == 'imo' and identifier in self.mock_vessels:
            vessel_data = self.mock_vessels[identifier]
            vessel = VesselDetails(**vessel_data)
            self._cache_vessel_data(cache_key, vessel)
            return vessel
        
        # Try real APIs
        vessel = None
        
        if self.marinetraffic_api_key:
            try:
                vessel = await self._get_marinetraffic_vessel(identifier, identifier_type)
            except Exception as e:
                logger.warning(f"MarineTraffic vessel lookup failed: {e}")
        
        if not vessel and self.vesselfinder_api_key:
            try:
                vessel = await self._get_vesselfinder_vessel(identifier, identifier_type)
            except Exception as e:
                logger.warning(f"VesselFinder vessel lookup failed: {e}")
        
        if not vessel and self.shipfinder_api_key:
            try:
                vessel = await self._get_shipfinder_vessel(identifier, identifier_type)
            except Exception as e:
                logger.warning(f"ShipFinder vessel lookup failed: {e}")
        
        if vessel:
            self._cache_vessel_data(cache_key, vessel)
        
        return vessel
    
    async def _get_vessel_position(self, vessel: VesselDetails) -> Optional[VesselPosition]:
        """Get current vessel position"""
        
        # Try real APIs first
        if self.marinetraffic_api_key:
            try:
                return await self._get_marinetraffic_position(vessel)
            except Exception as e:
                logger.warning(f"MarineTraffic position lookup failed: {e}")
        
        if self.vesselfinder_api_key:
            try:
                return await self._get_vesselfinder_position(vessel)
            except Exception as e:
                logger.warning(f"VesselFinder position lookup failed: {e}")
        
        # Fallback to mock position
        return self._get_mock_position(vessel)
    
    async def _get_position_history(
        self, 
        vessel: VesselDetails, 
        hours: int
    ) -> List[VesselPosition]:
        """Get vessel position history"""
        
        # Try real APIs first
        if self.marinetraffic_api_key:
            try:
                return await self._get_marinetraffic_history(vessel, hours)
            except Exception as e:
                logger.warning(f"MarineTraffic history lookup failed: {e}")
        
        # Fallback to mock history
        return self._get_mock_position_history(vessel, hours)
    
    async def _get_vessel_destination(
        self, 
        vessel: VesselDetails
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Get vessel destination and ETA"""
        
        # Try real APIs first
        if self.marinetraffic_api_key:
            try:
                return await self._get_marinetraffic_destination(vessel)
            except Exception as e:
                logger.warning(f"MarineTraffic destination lookup failed: {e}")
        
        # Fallback to mock destination
        return self._get_mock_destination(vessel)
    
    async def _get_vessel_route(self, vessel: VesselDetails) -> List[Tuple[float, float]]:
        """Get vessel route points"""
        
        # Try real APIs first
        if self.marinetraffic_api_key:
            try:
                return await self._get_marinetraffic_route(vessel)
            except Exception as e:
                logger.warning(f"MarineTraffic route lookup failed: {e}")
        
        # Fallback to mock route
        return self._get_mock_route(vessel)
    
    async def _get_vessel_weather(
        self, 
        position: VesselPosition
    ) -> Dict[str, Any]:
        """Get weather conditions at vessel position"""
        
        # This would integrate with the marine weather service
        # For now, return mock weather
        return {
            "wind_speed": 15.0,
            "wind_direction": 180.0,
            "wave_height": 2.5,
            "wave_direction": 190.0,
            "sea_state": "moderate",
            "visibility": 10.0,
            "temperature": 20.0
        }
    
    def _generate_vessel_alerts(
        self, 
        vessel: VesselDetails, 
        position: VesselPosition, 
        weather: Dict[str, Any]
    ) -> List[str]:
        """Generate alerts for vessel"""
        alerts = []
        
        # Speed alerts
        if position.speed > 25:
            alerts.append("High speed warning")
        elif position.speed < 1:
            alerts.append("Vessel appears stationary")
        
        # Weather alerts
        if weather.get('wave_height', 0) > 6.0:
            alerts.append("High wave warning")
        if weather.get('wind_speed', 0) > 25.0:
            alerts.append("High wind warning")
        if weather.get('visibility', 10) < 5.0:
            alerts.append("Low visibility warning")
        
        # Position alerts
        if position.latitude > 70 or position.latitude < -70:
            alerts.append("High latitude warning")
        
        return alerts
    
    async def _search_marinetraffic(self, query: str, limit: int) -> List[VesselDetails]:
        """Search vessels using MarineTraffic API"""
        if not self.marinetraffic_api_key:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.marinetraffic_base}/vessels"
                params = {
                    "api_key": self.marinetraffic_api_key,
                    "search": query,
                    "limit": limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_marinetraffic_search(data)
                    else:
                        logger.warning(f"MarineTraffic search failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"MarineTraffic search error: {e}")
            return []
    
    def _parse_marinetraffic_search(self, data: Dict[str, Any]) -> List[VesselDetails]:
        """Parse MarineTraffic search results"""
        vessels = []
        
        try:
            for vessel_data in data.get('data', []):
                vessel = VesselDetails(
                    imo=vessel_data.get('IMO', ''),
                    mmsi=vessel_data.get('MMSI', ''),
                    name=vessel_data.get('NAME', ''),
                    callsign=vessel_data.get('CALLSIGN', ''),
                    vessel_type=vessel_data.get('TYPE', ''),
                    flag=vessel_data.get('FLAG', ''),
                    gross_tonnage=vessel_data.get('GT', None),
                    length=vessel_data.get('LENGTH', None),
                    width=vessel_data.get('WIDTH', None),
                    draft=vessel_data.get('DRAUGHT', None),
                    year_built=vessel_data.get('YEAR_BUILT', None),
                    home_port=vessel_data.get('HOMEPORT', None),
                    operator=vessel_data.get('OPERATOR', None),
                    last_updated=datetime.now()
                )
                vessels.append(vessel)
        except Exception as e:
            logger.error(f"Failed to parse MarineTraffic data: {e}")
        
        return vessels
    
    async def _get_marinetraffic_vessel(
        self, 
        identifier: str, 
        identifier_type: str
    ) -> Optional[VesselDetails]:
        """Get vessel details from MarineTraffic"""
        # Implementation would call MarineTraffic vessel details API
        return None
    
    async def _get_marinetraffic_position(self, vessel: VesselDetails) -> Optional[VesselPosition]:
        """Get vessel position from MarineTraffic"""
        # Implementation would call MarineTraffic position API
        return None
    
    async def _get_marinetraffic_history(
        self, 
        vessel: VesselDetails, 
        hours: int
    ) -> List[VesselPosition]:
        """Get vessel position history from MarineTraffic"""
        # Implementation would call MarineTraffic history API
        return []
    
    async def _get_marinetraffic_destination(
        self, 
        vessel: VesselDetails
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Get vessel destination from MarineTraffic"""
        # Implementation would call MarineTraffic destination API
        return None, None
    
    async def _get_marinetraffic_route(self, vessel: VesselDetails) -> List[Tuple[float, float]]:
        """Get vessel route from MarineTraffic"""
        # Implementation would call MarineTraffic route API
        return []
    
    # Similar methods for other APIs (VesselFinder, ShipFinder, AIS)
    async def _get_vesselfinder_vessel(
        self, 
        identifier: str, 
        identifier_type: str
    ) -> Optional[VesselDetails]:
        return None
    
    async def _get_vesselfinder_position(self, vessel: VesselDetails) -> Optional[VesselPosition]:
        return None
    
    async def _get_shipfinder_vessel(
        self, 
        identifier: str, 
        identifier_type: str
    ) -> Optional[VesselDetails]:
        return None
    
    async def _get_shipfinder_position(self, vessel: VesselDetails) -> Optional[VesselPosition]:
        return None
    
    def _get_mock_position(self, vessel: VesselDetails) -> VesselPosition:
        """Generate mock vessel position"""
        # Generate realistic mock position based on vessel type
        if "container" in vessel.vessel_type.lower():
            # Container ships typically operate in major shipping lanes
            lat = 51.9244 + (hash(vessel.imo) % 100 - 50) * 0.01  # Around Rotterdam
            lng = 4.4777 + (hash(vessel.imo) % 100 - 50) * 0.01
        else:
            # Other vessels get random positions
            lat = 20.0 + (hash(vessel.imo) % 60 - 30)
            lng = -60.0 + (hash(vessel.imo) % 120 - 60)
        
        return VesselPosition(
            timestamp=datetime.now(),
            latitude=lat,
            longitude=lng,
            speed=12.0 + (hash(vessel.imo) % 20),  # 12-32 knots
            heading=hash(vessel.imo) % 360,
            course=hash(vessel.imo) % 360,
            status="Under Way Using Engine",
            source="Mock"
        )
    
    def _get_mock_position_history(
        self, 
        vessel: VesselDetails, 
        hours: int
    ) -> List[VesselPosition]:
        """Generate mock position history"""
        history = []
        current_time = datetime.now()
        
        # Generate positions every hour for the specified duration
        for hour in range(hours, 0, -1):
            timestamp = current_time - timedelta(hours=hour)
            
            # Simulate vessel movement
            base_lat = 51.9244  # Start near Rotterdam
            base_lng = 4.4777
            
            # Add some realistic movement
            lat = base_lat + (hour * 0.01) + (hash(vessel.imo + str(hour)) % 100 - 50) * 0.001
            lng = base_lng + (hour * 0.02) + (hash(vessel.imo + str(hour)) % 100 - 50) * 0.001
            
            position = VesselPosition(
                timestamp=timestamp,
                latitude=lat,
                longitude=lng,
                speed=10.0 + (hash(vessel.imo + str(hour)) % 15),
                heading=hash(vessel.imo + str(hour)) % 360,
                course=hash(vessel.imo + str(hour)) % 360,
                status="Under Way Using Engine",
                source="Mock"
            )
            
            history.append(position)
        
        return history
    
    def _get_mock_destination(
        self, 
        vessel: VesselDetails
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Generate mock destination and ETA"""
        destinations = [
            "Port of Singapore",
            "Port of Shanghai", 
            "Port of Los Angeles",
            "Port of New York",
            "Port of Hamburg",
            "Port of Antwerp"
        ]
        
        destination = destinations[hash(vessel.imo) % len(destinations)]
        eta = datetime.now() + timedelta(days=hash(vessel.imo) % 14 + 3)  # 3-17 days
        
        return destination, eta
    
    def _get_mock_route(self, vessel: VesselDetails) -> List[Tuple[float, float]]:
        """Generate mock route points"""
        # Generate a simple route from current position to destination
        route = []
        
        # Start near Rotterdam
        start_lat, start_lng = 51.9244, 4.4777
        
        # Add waypoints
        waypoints = [
            (49.0, -5.0),   # English Channel
            (36.0, -6.0),   # Mediterranean
            (31.0, 32.0),   # Suez Canal
            (15.0, 65.0),   # Arabian Sea
            (1.0, 103.0),   # Singapore
        ]
        
        route.append((start_lat, start_lng))
        route.extend(waypoints)
        
        return route
    
    def _deduplicate_vessels(self, vessels: List[VesselDetails]) -> List[VesselDetails]:
        """Remove duplicate vessels from search results"""
        seen_imos = set()
        unique_vessels = []
        
        for vessel in vessels:
            if vessel.imo and vessel.imo not in seen_imos:
                seen_imos.add(vessel.imo)
                unique_vessels.append(vessel)
            elif not vessel.imo and vessel.mmsi and vessel.mmsi not in seen_imos:
                seen_imos.add(vessel.mmsi)
                unique_vessels.append(vessel)
        
        return unique_vessels
    
    def _cache_vessel_data(self, key: str, data: Any):
        """Cache vessel data"""
        self.vessel_cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    async def get_fleet_overview(self, fleet_ids: List[str]) -> List[VesselTrack]:
        """Get overview of multiple vessels (fleet tracking)"""
        fleet_tracks = []
        
        for vessel_id in fleet_ids:
            track = await self.track_vessel(vessel_id, include_history=False)
            if track:
                fleet_tracks.append(track)
        
        return fleet_tracks
    
    async def get_vessel_alerts(self, vessel_id: str) -> List[str]:
        """Get current alerts for a specific vessel"""
        track = await self.track_vessel(vessel_id, include_history=False)
        if track:
            return track.alerts
        return []
    
    async def get_vessel_weather_report(self, vessel_id: str) -> Dict[str, Any]:
        """Get detailed weather report for vessel's current position"""
        track = await self.track_vessel(vessel_id, include_history=False)
        if track and track.weather_conditions:
            return track.weather_conditions
        return {}

# Global instance
enhanced_vessel_tracker = EnhancedVesselTracker()
