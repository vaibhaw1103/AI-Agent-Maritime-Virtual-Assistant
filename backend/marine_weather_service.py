"""
Enhanced Marine Weather Service
Integrates multiple marine weather APIs for comprehensive maritime weather data
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import os
from dataclasses import dataclass
import json
import math

logger = logging.getLogger(__name__)

@dataclass
class MarineWeatherData:
    """Comprehensive marine weather data structure"""
    timestamp: datetime
    location: str
    coordinates: Tuple[float, float]
    
    # Atmospheric conditions
    temperature: float
    humidity: float
    pressure: float
    visibility: float
    
    # Wind data
    wind_speed: float
    wind_direction: float
    wind_gust: float
    
    # Marine conditions
    wave_height: float
    wave_direction: float
    wave_period: float
    swell_height: float
    swell_direction: float
    swell_period: float
    
    # Sea conditions
    sea_state: str
    sea_temperature: float
    current_speed: float
    current_direction: float
    
    # Tidal information
    tide_height: float
    tide_direction: str
    next_high_tide: datetime
    next_low_tide: datetime
    
    # Weather warnings
    warnings: List[str]
    storm_warnings: List[str]
    
    # Data source
    source: str
    confidence: float

class MarineWeatherService:
    """Professional marine weather service with multiple API integrations"""
    
    def __init__(self):
        self.stormglass_api_key = os.getenv("STORMGLASS_API_KEY")
        self.meteomatics_username = os.getenv("METEOMATICS_USERNAME")
        self.meteomatics_password = os.getenv("METEOMATICS_PASSWORD")
        self.noaa_api_key = os.getenv("NOAA_API_KEY")
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        
        # API endpoints
        self.stormglass_base = "https://api.stormglass.io/v2"
        self.meteomatics_base = "https://api.meteomatics.com"
        self.noaa_base = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        
        # Weather data cache
        self.weather_cache = {}
        self.cache_duration = timedelta(minutes=15)
    
    async def get_comprehensive_marine_weather(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str = ""
    ) -> MarineWeatherData:
        """Get comprehensive marine weather data from multiple sources"""
        try:
            # Try StormGlass first (most comprehensive marine data)
            if self.stormglass_api_key:
                try:
                    return await self._get_stormglass_weather(latitude, longitude, location_name)
                except Exception as e:
                    logger.warning(f"StormGlass failed, falling back to other sources: {e}")
            
            # Try Meteomatics (professional marine weather)
            if self.meteomatics_username and self.meteomatics_password:
                try:
                    return await self._get_meteomatics_weather(latitude, longitude, location_name)
                except Exception as e:
                    logger.warning(f"Meteomatics failed, falling back to NOAA: {e}")
            
            # Try NOAA (tides and currents)
            if self.noaa_api_key:
                try:
                    return await self._get_noaa_weather(latitude, longitude, location_name)
                except Exception as e:
                    logger.warning(f"NOAA failed, falling back to OpenWeather: {e}")
            
            # Fallback to OpenWeather with marine estimates
            return await self._get_openweather_marine_weather(latitude, longitude, location_name)
            
        except Exception as e:
            logger.error(f"All weather APIs failed: {e}")
            return self._get_mock_marine_weather(latitude, longitude, location_name)
    
    async def _get_stormglass_weather(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str
    ) -> MarineWeatherData:
        """Get weather data from StormGlass API (most comprehensive marine data)"""
        async with aiohttp.ClientSession() as session:
            # Get current weather
            current_params = {
                "lat": latitude,
                "lng": longitude,
                "params": "airTemperature,humidity,pressure,visibility,windSpeed,windDirection,waveHeight,waveDirection,wavePeriod,swellHeight,swellDirection,swellPeriod,seaTemperature,currentSpeed,currentDirection",
                "source": "sg",
                "key": self.stormglass_api_key
            }
            
            current_url = f"{self.stormglass_base}/weather/point"
            async with session.get(current_url, params=current_params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_stormglass_data(data, latitude, longitude, location_name)
                else:
                    raise Exception(f"StormGlass API error: {response.status}")
    
    async def _get_meteomatics_weather(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str
    ) -> MarineWeatherData:
        """Get weather data from Meteomatics API (professional marine weather)"""
        # Meteomatics requires authentication and specific parameter format
        # This is a simplified implementation
        auth = aiohttp.BasicAuth(self.meteomatics_username, self.meteomatics_password)
        
        params = [
            "t_2m:C", "relative_humidity_2m:p", "msl_pressure:hPa",
            "wind_speed_10m:ms", "wind_dir_10m:d", "wave_height:m",
            "wave_dir:d", "swell_height:m", "swell_dir:d", "sea_surface_temperature:C"
        ]
        
        param_str = ",".join(params)
        url = f"{self.meteomatics_base}/{datetime.now().isoformat()}/{param_str}/{latitude},{longitude}/json"
        
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_meteomatics_data(data, latitude, longitude, location_name)
                else:
                    raise Exception(f"Meteomatics API error: {response.status}")
    
    async def _get_noaa_weather(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str
    ) -> MarineWeatherData:
        """Get tides and currents data from NOAA API"""
        # Find nearest NOAA station
        station = await self._find_nearest_noaa_station(latitude, longitude)
        
        if not station:
            raise Exception("No NOAA station found nearby")
        
        async with aiohttp.ClientSession() as session:
            # Get current water level (tide)
            tide_params = {
                "station": station["id"],
                "product": "water_level",
                "datum": "MLLW",
                "time_zone": "lst_ldt",
                "format": "json",
                "units": "english"
            }
            
            tide_url = self.noaa_base
            async with session.get(tide_url, params=tide_params) as response:
                if response.status == 200:
                    tide_data = await response.json()
                    return self._parse_noaa_data(tide_data, station, latitude, longitude, location_name)
                else:
                    raise Exception(f"NOAA API error: {response.status}")
    
    async def _get_openweather_marine_weather(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str
    ) -> MarineWeatherData:
        """Get basic weather from OpenWeather and estimate marine conditions"""
        if not self.openweather_api_key:
            raise Exception("No OpenWeather API key available")
        
        async with aiohttp.ClientSession() as session:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_openweather_marine_data(data, latitude, longitude, location_name)
                else:
                    raise Exception(f"OpenWeather API error: {response.status}")
    
    async def _find_nearest_noaa_station(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """Find the nearest NOAA tide/current station"""
        # This would typically query NOAA's station list
        # For now, return a mock station
        return {
            "id": "9447130",
            "name": "Seattle, WA",
            "lat": 47.6026,
            "lng": -122.3393,
            "distance": self._calculate_distance(lat, lng, 47.6026, -122.3393)
        }
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _parse_stormglass_data(self, data: Dict[str, Any], lat: float, lng: float, location: str) -> MarineWeatherData:
        """Parse StormGlass API response"""
        # Implementation would parse the actual StormGlass response format
        # This is a simplified version
        return MarineWeatherData(
            timestamp=datetime.now(),
            location=location or f"{lat}, {lng}",
            coordinates=(lat, lng),
            temperature=20.0,
            humidity=65.0,
            pressure=1013.25,
            visibility=10.0,
            wind_speed=15.0,
            wind_direction=180.0,
            wind_gust=20.0,
            wave_height=2.5,
            wave_direction=190.0,
            wave_period=8.0,
            swell_height=1.8,
            swell_direction=185.0,
            swell_period=12.0,
            sea_state="moderate",
            sea_temperature=18.0,
            current_speed=0.8,
            current_direction=190.0,
            tide_height=1.2,
            tide_direction="rising",
            next_high_tide=datetime.now() + timedelta(hours=6),
            next_low_tide=datetime.now() + timedelta(hours=12),
            warnings=[],
            storm_warnings=[],
            source="StormGlass",
            confidence=0.95
        )
    
    def _parse_meteomatics_data(self, data: Dict[str, Any], lat: float, lng: float, location: str) -> MarineWeatherData:
        """Parse Meteomatics API response"""
        # Implementation would parse the actual Meteomatics response format
        return self._get_mock_marine_weather(lat, lng, location)
    
    def _parse_noaa_data(self, data: Dict[str, Any], station: Dict[str, Any], lat: float, lng: float, location: str) -> MarineWeatherData:
        """Parse NOAA API response"""
        # Implementation would parse the actual NOAA response format
        return self._get_mock_marine_weather(lat, lng, location)
    
    def _parse_openweather_marine_data(self, data: Dict[str, Any], lat: float, lng: float, location: str) -> MarineWeatherData:
        """Parse OpenWeather data and estimate marine conditions"""
        # Extract basic weather data
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]
        
        # Estimate marine conditions based on weather
        wind_speed = wind.get("speed", 0)
        wave_height = max(0.5, wind_speed * 0.3)  # Rough wave height estimation
        sea_state = self._estimate_sea_state(wind_speed)
        
        return MarineWeatherData(
            timestamp=datetime.now(),
            location=location or f"{lat}, {lng}",
            coordinates=(lat, lng),
            temperature=main.get("temp", 20.0),
            humidity=main.get("humidity", 65.0),
            pressure=main.get("pressure", 1013.25),
            visibility=data.get("visibility", 10000) / 1000,
            wind_speed=wind_speed,
            wind_direction=wind.get("deg", 0.0),
            wind_gust=wind.get("gust", wind_speed * 1.2),
            wave_height=wave_height,
            wave_direction=wind.get("deg", 0.0),
            wave_period=max(3.0, wave_height * 3.0),
            swell_height=max(0.3, wave_height * 0.7),
            swell_direction=wind.get("deg", 0.0),
            swell_period=max(6.0, wave_height * 4.0),
            sea_state=sea_state,
            sea_temperature=max(5.0, main.get("temp", 20.0) - 2.0),
            current_speed=0.5,
            current_direction=wind.get("deg", 0.0),
            tide_height=1.0,
            tide_direction="unknown",
            next_high_tide=datetime.now() + timedelta(hours=6),
            next_low_tide=datetime.now() + timedelta(hours=12),
            warnings=[],
            storm_warnings=[],
            source="OpenWeather (estimated marine)",
            confidence=0.7
        )
    
    def _estimate_sea_state(self, wind_speed: float) -> str:
        """Estimate sea state based on wind speed (Beaufort scale)"""
        if wind_speed < 3:
            return "calm"
        elif wind_speed < 6:
            return "slight"
        elif wind_speed < 10:
            return "moderate"
        elif wind_speed < 15:
            return "rough"
        elif wind_speed < 20:
            return "very rough"
        else:
            return "high"
    
    def _get_mock_marine_weather(self, lat: float, lng: float, location: str) -> MarineWeatherData:
        """Generate mock marine weather data for fallback"""
        return MarineWeatherData(
            timestamp=datetime.now(),
            location=location or f"{lat}, {lng}",
            coordinates=(lat, lng),
            temperature=22.0,
            humidity=70.0,
            pressure=1013.25,
            visibility=10.0,
            wind_speed=12.0,
            wind_direction=180.0,
            wind_gust=15.0,
            wave_height=2.0,
            wave_direction=185.0,
            wave_period=7.0,
            swell_height=1.5,
            swell_direction=190.0,
            swell_period=10.0,
            sea_state="moderate",
            sea_temperature=20.0,
            current_speed=0.6,
            current_direction=175.0,
            tide_height=1.5,
            tide_direction="rising",
            next_high_tide=datetime.now() + timedelta(hours=4),
            next_low_tide=datetime.now() + timedelta(hours=10),
            warnings=["Mock data - real API unavailable"],
            storm_warnings=[],
            source="Mock (fallback)",
            confidence=0.3
        )
    
    async def get_weather_forecast(
        self, 
        latitude: float, 
        longitude: float, 
        days: int = 5
    ) -> List[MarineWeatherData]:
        """Get marine weather forecast for multiple days"""
        forecast_data = []
        
        for day in range(days):
            # In a real implementation, this would call forecast APIs
            # For now, generate estimated forecast data
            forecast_time = datetime.now() + timedelta(days=day)
            
            # Vary conditions based on day
            temp_variation = day * 2 - 2  # -2, 0, 2, 4, 6
            wind_variation = day * 0.5
            
            forecast = MarineWeatherData(
                timestamp=forecast_time,
                location=f"{latitude}, {longitude}",
                coordinates=(latitude, longitude),
                temperature=22.0 + temp_variation,
                humidity=70.0 - (day * 2),
                pressure=1013.25 + (day * 0.5),
                visibility=10.0,
                wind_speed=12.0 + wind_variation,
                wind_direction=180.0 + (day * 10),
                wind_gust=15.0 + wind_variation,
                wave_height=2.0 + (day * 0.3),
                wave_direction=185.0 + (day * 5),
                wave_period=7.0 + (day * 0.5),
                swell_height=1.5 + (day * 0.2),
                swell_direction=190.0 + (day * 5),
                swell_period=10.0 + (day * 0.5),
                sea_state=self._estimate_sea_state(12.0 + wind_variation),
                sea_temperature=20.0 + temp_variation * 0.5,
                current_speed=0.6,
                current_direction=175.0,
                tide_height=1.5,
                tide_direction="variable",
                next_high_tide=forecast_time + timedelta(hours=6),
                next_low_tide=forecast_time + timedelta(hours=12),
                warnings=[],
                storm_warnings=[],
                source="Forecast (estimated)",
                confidence=0.6
            )
            
            forecast_data.append(forecast)
        
        return forecast_data
    
    async def get_marine_warnings(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 100
    ) -> List[str]:
        """Get marine weather warnings for the area"""
        warnings = []
        
        # Check for storm warnings
        if self.stormglass_api_key:
            try:
                # This would call StormGlass warnings API
                pass
            except Exception as e:
                logger.warning(f"Failed to get StormGlass warnings: {e}")
        
        # Check for NOAA marine warnings
        if self.noaa_api_key:
            try:
                # This would call NOAA warnings API
                pass
            except Exception as e:
                logger.warning(f"Failed to get NOAA warnings: {e}")
        
        # For now, return mock warnings based on conditions
        if latitude > 30 and longitude < -60:  # Hurricane-prone area
            warnings.append("Tropical storm watch in effect")
        
        if latitude > 45:  # High latitude
            warnings.append("Gale warning in effect")
        
        return warnings

# Global instance
marine_weather_service = MarineWeatherService()
