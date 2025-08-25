'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Ship, 
  MapPin, 
  Navigation, 
  Wind, 
  Waves, 
  Anchor, 
  Compass,
  Layers,
  Settings,
  Info,
  AlertTriangle,
  CheckCircle,
  Clock,
  Fuel,
  Route
} from 'lucide-react';

// Fix for Leaflet markers in Next.js
import L from 'leaflet';
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom ship icon
const shipIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIwIDIxVjNMMTMgMTBMMTAgN0w0IDEzVjIxSDBWMTlIMlYxNUw4IDIxSDE2TDIyIDE1VjE5SDI0VjIxSDIwWiIgZmlsbD0iIzFlNDBhZiIvPgo8L3N2Zz4K',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
  popupAnchor: [0, -12]
});

interface MarineWeatherData {
  wind_speed: number;
  wind_direction: number;
  wave_height: number;
  temperature: number;
  visibility: number;
  pressure: number;
  storm_warnings: string[];
}

interface RouteSegment {
  start: [number, number];
  end: [number, number];
  distance_nm: number;
  estimated_time_hours: number;
  fuel_consumption_mt: number;
  weather_conditions: MarineWeatherData;
  hazards: string[];
}

interface OptimizedRoute {
  origin: [number, number];
  destination: [number, number];
  waypoints: [number, number][];
  segments: RouteSegment[];
  total_distance_nm: number;
  total_time_hours: number;
  total_fuel_mt: number;
  optimization_mode: string;
  weather_warnings: string[];
  safety_score: number;
  route_type: string;
  estimated_arrival: string;
  alternative_routes: any[];
}

interface VesselPosition {
  id: string;
  position: [number, number];
  heading: number;
  speed: number;
  vessel_type: string;
}

interface FreeMarineMapProps {
  routes?: OptimizedRoute[];
  weatherData?: MarineWeatherData;
  vesselPositions?: VesselPosition[];
  onRouteSelect?: (route: OptimizedRoute) => void;
  className?: string;
}

// Free map tile providers
const FREE_MAP_TILES = {
  openstreetmap: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  maritime: 'https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  nautical: 'https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png'
};

export default function FreeMarineMap({
  routes = [],
  weatherData,
  vesselPositions = [],
  onRouteSelect,
  className = "w-full h-full"
}: FreeMarineMapProps) {
  const [mapStyle, setMapStyle] = useState('openstreetmap');
  const [activeLayers, setActiveLayers] = useState({
    bathymetry: true,
    shipping_lanes: true,
    weather: true,
    vessels: true,
    routes: true
  });
  const [selectedRoute, setSelectedRoute] = useState<OptimizedRoute | null>(null);
  const [showRouteInfo, setShowRouteInfo] = useState(false);
  const [center, setCenter] = useState<[number, number]>([30, 0]);
  const [zoom, setZoom] = useState(2);

  useEffect(() => {
    if (routes.length > 0) {
      const allPoints = routes.flatMap(route => [
        route.origin,
        route.destination,
        ...route.waypoints
      ]);
      if (allPoints.length > 0) {
        const lats = allPoints.map(p => p[0]);
        const lngs = allPoints.map(p => p[1]);
        const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
        const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
        setCenter([centerLat, centerLng]);
        setZoom(4);
      }
    }
  }, [routes]);

  const generateRoutePolyline = useCallback((route: OptimizedRoute) => {
    const points = [route.origin, ...route.waypoints, route.destination];
    return points.filter(point => point[0] !== 0 && point[1] !== 0);
  }, []);

  const getRouteColor = (safetyScore: number) => {
    if (safetyScore >= 0.8) return '#10b981'; // Green
    if (safetyScore >= 0.6) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const handleRouteClick = (route: OptimizedRoute) => {
    setSelectedRoute(route);
    setShowRouteInfo(true);
    onRouteSelect?.(route);
  };

  return (
    <div className={`${className} relative bg-gray-900 rounded-lg overflow-hidden`}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ width: '100%', height: '100%' }}
        className="z-0"
      >
        {/* Free OpenStreetMap Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={FREE_MAP_TILES.openstreetmap as any}
        />
        
        {/* Free Maritime Overlay */}
        {activeLayers.bathymetry && (
          <TileLayer
            attribution='&copy; <a href="https://www.openseamap.org/">OpenSeaMap</a>'
            url={FREE_MAP_TILES.maritime as any}
            opacity={0.6}
          />
        )}

        {/* Routes */}
        {activeLayers.routes && routes.map((route, index) => (
          <Polyline
            key={`route-${index}`}
            positions={generateRoutePolyline(route)}
            color={getRouteColor(route.safety_score)}
            weight={6}
            opacity={0.8}
            eventHandlers={{
              click: () => handleRouteClick(route)
            }}
            style={{ cursor: 'pointer' }}
          />
        ))}

        {/* Vessels */}
        {activeLayers.vessels && vesselPositions.map((vessel, index) => (
          <Marker
            key={`vessel-${index}`}
            position={vessel.position}
            icon={shipIcon}
            rotationAngle={vessel.heading}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-semibold">{vessel.vessel_type}</h3>
                <p>Speed: {vessel.speed} knots</p>
                <p>Heading: {vessel.heading}°</p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Weather Overlay */}
        {activeLayers.weather && weatherData && (
          <Circle
            center={center}
            radius={500000}
            pathOptions={{
              color: weatherData.wind_speed > 20 ? '#ef4444' : 
                     weatherData.wind_speed > 10 ? '#f59e0b' : '#10b981',
              fillColor: weatherData.wind_speed > 20 ? '#fecaca' : 
                        weatherData.wind_speed > 10 ? '#fef3c7' : '#d1fae5',
              fillOpacity: 0.3,
              weight: 2
            }}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-semibold">Weather Conditions</h3>
                <p>Wind: {weatherData.wind_speed} m/s</p>
                <p>Waves: {weatherData.wave_height}m</p>
                <p>Temp: {weatherData.temperature}°C</p>
              </div>
            </Popup>
          </Circle>
        )}
      </MapContainer>

      {/* Map Controls Panel */}
      <div className="absolute top-4 right-4 space-y-2">
        <Card className="w-64 bg-white/95 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Layers className="w-5 h-5" />
              Map Layers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.bathymetry}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, bathymetry: e.target.checked }))}
                  className="rounded"
                />
                Bathymetry
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.weather}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, weather: e.target.checked }))}
                  className="rounded"
                />
                Weather
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.vessels}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, vessels: e.target.checked }))}
                  className="rounded"
                />
                Vessels
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.routes}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, routes: e.target.checked }))}
                  className="rounded"
                />
                Routes
              </label>
            </div>
            
            <div className="pt-2 border-t">
              <label className="text-sm font-medium">Map Style:</label>
              <select
                value={mapStyle}
                onChange={(e) => setMapStyle(e.target.value)}
                className="w-full mt-1 p-2 border rounded text-sm"
              >
                <option value="openstreetmap">OpenStreetMap</option>
                <option value="maritime">Maritime</option>
                <option value="satellite">Satellite</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Route Information Panel */}
      {showRouteInfo && selectedRoute && (
        <div className="absolute bottom-4 left-4 w-80">
          <Card className="bg-white/95 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">Route Details</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRouteInfo(false)}
                className="h-6 w-6 p-0"
              >
                ×
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="font-medium">Distance:</span>
                  <p>{selectedRoute.total_distance_nm.toFixed(1)} nm</p>
                </div>
                <div>
                  <span className="font-medium">Time:</span>
                  <p>{selectedRoute.total_time_hours.toFixed(1)} hours</p>
                </div>
                <div>
                  <span className="font-medium">Fuel:</span>
                  <p>{selectedRoute.total_fuel_mt.toFixed(1)} MT</p>
                </div>
                <div>
                  <span className="font-medium">Mode:</span>
                  <p className="capitalize">{selectedRoute.optimization_mode}</p>
                </div>
              </div>
              
              <div className="space-y-1">
                <span className="font-medium text-sm">Safety Score:</span>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${selectedRoute.safety_score * 100}%`,
                        backgroundColor: getRouteColor(selectedRoute.safety_score)
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {(selectedRoute.safety_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {selectedRoute.weather_warnings.length > 0 && (
                <div className="space-y-1">
                  <span className="font-medium text-sm flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-orange-500" />
                    Weather Warnings:
                  </span>
                  <div className="space-y-1">
                    {selectedRoute.weather_warnings.map((warning, index) => (
                      <Badge key={index} variant="destructive" className="text-xs">
                        {warning}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button size="sm" className="flex-1">
                  <Navigation className="w-4 h-4 mr-2" />
                  Navigate
                </Button>
                <Button size="sm" variant="outline" className="flex-1">
                  <Info className="w-4 h-4 mr-2" />
                  Details
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Status Bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 text-white text-xs px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span>🌊 Free Marine Map</span>
          <span>📍 {center[0].toFixed(2)}°, {center[1].toFixed(2)}°</span>
          <span>🔍 Zoom: {zoom}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-green-400" />
            OpenStreetMap
          </span>
          <span className="flex items-center gap-1">
            <Ship className="w-3 h-3 text-blue-400" />
            {vesselPositions.length} vessels
          </span>
        </div>
      </div>
    </div>
  );
}
