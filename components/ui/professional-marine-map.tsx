'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Map, { 
  NavigationControl, 
  FullscreenControl, 
  Source, 
  Layer,
  Marker,
  Popup,
  useMap
} from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
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

// Mapbox access token
const MAPBOX_ACCESS_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || 'your-mapbox-token-here';

// Professional marine map styles
const MARINE_MAP_STYLES = {
  nautical: 'mapbox://styles/mapbox/satellite-v9',
  marine: 'mapbox://styles/mapbox/streets-v12',
  dark: 'mapbox://styles/mapbox/dark-v11',
  light: 'mapbox://styles/mapbox/light-v11'
};

// Marine-specific layer configurations
const MARINE_LAYERS = {
  bathymetry: {
    id: 'bathymetry',
    type: 'fill' as const,
    paint: {
      'fill-color': [
        'interpolate',
        ['linear'],
        ['get', 'depth'],
        0, '#e6f3ff',
        100, '#b3d9ff',
        500, '#80bfff',
        1000, '#4da6ff',
        2000, '#1a8cff',
        4000, '#0073e6',
        6000, '#0059b3',
        8000, '#004080'
      ],
      'fill-opacity': 0.6
    }
  },
  shipping_lanes: {
    id: 'shipping-lanes',
    type: 'line' as const,
    paint: {
      'line-color': '#ff6b35',
      'line-width': 3,
      'line-opacity': 0.8,
      'line-dasharray': [2, 2]
    }
  },
  weather_overlay: {
    id: 'weather-overlay',
    type: 'symbol' as const,
    layout: {
      'icon-image': 'wind-arrow',
      'icon-size': 1.5,
      'icon-rotate': ['get', 'wind-direction'],
      'icon-allow-overlap': true
    },
    paint: {
      'icon-color': [
        'interpolate',
        ['linear'],
        ['get', 'wind-speed'],
        0, '#00ff00',
        10, '#ffff00',
        20, '#ff8000',
        30, '#ff0000'
      ]
    }
  }
};

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
  alternative_routes: [number, number][][];
}

interface ProfessionalMarineMapProps {
  routes?: OptimizedRoute[];
  weatherData?: MarineWeatherData;
  vesselPositions?: Array<{
    id: string;
    position: [number, number];
    heading: number;
    speed: number;
    vessel_type: string;
  }>;
  onRouteSelect?: (route: OptimizedRoute) => void;
  className?: string;
}

export default function ProfessionalMarineMap({
  routes = [],
  weatherData,
  vesselPositions = [],
  onRouteSelect,
  className = "w-full h-full"
}: ProfessionalMarineMapProps) {
  const [viewState, setViewState] = useState({
    longitude: 0,
    latitude: 30,
    zoom: 2
  });
  
  const [mapStyle, setMapStyle] = useState(MARINE_MAP_STYLES.marine);
  const [activeLayers, setActiveLayers] = useState({
    bathymetry: true,
    shipping_lanes: true,
    weather: true,
    vessels: true,
    routes: true
  });
  
  const [selectedRoute, setSelectedRoute] = useState<OptimizedRoute | null>(null);
  const [showRouteInfo, setShowRouteInfo] = useState(false);

  // Initialize map to center on major shipping area
  useEffect(() => {
    if (routes.length > 0) {
      const firstRoute = routes[0];
      setViewState({
        longitude: (firstRoute.origin[1] + firstRoute.destination[1]) / 2,
        latitude: (firstRoute.origin[0] + firstRoute.destination[0]) / 2,
        zoom: 4
      });
    }
  }, [routes]);

  // Generate route GeoJSON for display
  const generateRouteGeoJSON = useCallback((route: OptimizedRoute) => {
    const coordinates = [route.origin, ...route.waypoints, route.destination];
    
    return {
      type: 'Feature',
      properties: {
        route_id: route.route_type,
        optimization_mode: route.optimization_mode,
        safety_score: route.safety_score,
        total_distance: route.total_distance_nm,
        total_time: route.total_time_hours
      },
      geometry: {
        type: 'LineString',
        coordinates: coordinates.map(coord => [coord[1], coord[0]]) // Convert lat,lng to lng,lat
      }
    };
  }, []);

  // Generate weather overlay data
  const generateWeatherOverlay = useCallback(() => {
    if (!weatherData) return null;
    
    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            'wind-speed': weatherData.wind_speed,
            'wind-direction': weatherData.wind_direction,
            'wave-height': weatherData.wave_height
          },
          geometry: {
            type: 'Point',
            coordinates: [viewState.longitude, viewState.latitude]
          }
        }
      ]
    };
  }, [weatherData, viewState]);

  // Handle route selection
  const handleRouteClick = (route: OptimizedRoute) => {
    setSelectedRoute(route);
    setShowRouteInfo(true);
    onRouteSelect?.(route);
  };

  // Calculate route color based on safety score
  const getRouteColor = (safetyScore: number) => {
    if (safetyScore >= 0.8) return '#10b981'; // Green
    if (safetyScore >= 0.6) return '#f59e0b'; // Yellow
    if (safetyScore >= 0.4) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  return (
    <div className={`${className} relative bg-gray-900 rounded-lg overflow-hidden`}>
      {/* Map Container */}
      <Map
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        mapStyle={mapStyle}
        mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
        style={{ width: '100%', height: '100%' }}
        attributionControl={false}
        logoPosition="bottom-right"
      >
        {/* Navigation Controls */}
        <NavigationControl position="top-left" />
        <FullscreenControl position="top-left" />
        
        {/* Route Layers */}
        {routes.map((route, index) => (
          <Source
            key={`route-${index}`}
            id={`route-source-${index}`}
            type="geojson"
            data={generateRouteGeoJSON(route)}
          >
            <Layer
              id={`route-layer-${index}`}
              type="line"
              paint={{
                'line-color': getRouteColor(route.safety_score),
                'line-width': 4,
                'line-opacity': 0.8,
                'line-dasharray': route.optimization_mode === 'weather' ? [5, 5] : [1, 0]
              }}
              onClick={() => handleRouteClick(route)}
              style={{ cursor: 'pointer' }}
            />
            
            {/* Route Markers */}
            <Layer
              id={`route-markers-${index}`}
              type="symbol"
              layout={{
                'icon-image': 'marker',
                'icon-size': 0.8,
                'icon-allow-overlap': true
              }}
              paint={{
                'icon-color': getRouteColor(route.safety_score)
              }}
            />
          </Source>
        ))}
        
        {/* Weather Overlay */}
        {activeLayers.weather && weatherData && (
          <Source
            id="weather-overlay"
            type="geojson"
            data={generateWeatherOverlay()}
          >
            <Layer {...MARINE_LAYERS.weather_overlay} />
          </Source>
        )}
        
        {/* Vessel Markers */}
        {activeLayers.vessels && vesselPositions.map((vessel, index) => (
          <Marker
            key={`vessel-${index}`}
            longitude={vessel.position[1]}
            latitude={vessel.position[0]}
            anchor="center"
          >
            <div className="relative">
              <div 
                className="w-6 h-6 bg-blue-600 rounded-full border-2 border-white shadow-lg flex items-center justify-center"
                style={{
                  transform: `rotate(${vessel.heading}deg)`
                }}
              >
                <Ship className="w-4 h-4 text-white" />
              </div>
              <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                {vessel.vessel_type}
              </div>
            </div>
          </Marker>
        ))}
      </Map>

      {/* Map Controls Panel */}
      <div className="absolute top-4 right-4 space-y-2">
        {/* Map Style Selector */}
        <Card className="w-64 bg-white/95 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="w-4 h-4" />
              Map Layers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-2">
              {Object.entries(activeLayers).map(([layer, active]) => (
                <label key={layer} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={(e) => setActiveLayers(prev => ({
                      ...prev,
                      [layer]: e.target.checked
                    }))}
                    className="rounded"
                  />
                  <span className="capitalize">{layer.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
            
            <div className="pt-2 border-t">
              <label className="text-sm font-medium">Map Style</label>
              <select
                value={mapStyle}
                onChange={(e) => setMapStyle(e.target.value)}
                className="w-full mt-1 text-sm border rounded px-2 py-1"
              >
                <option value={MARINE_MAP_STYLES.marine}>Marine</option>
                <option value={MARINE_MAP_STYLES.nautical}>Nautical</option>
                <option value={MARINE_MAP_STYLES.dark}>Dark</option>
                <option value={MARINE_MAP_STYLES.light}>Light</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Route Information Panel */}
      {showRouteInfo && selectedRoute && (
        <div className="absolute bottom-4 left-4 w-80">
          <Card className="bg-white/95 backdrop-blur-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Route className="w-4 h-4" />
                  Route Details
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRouteInfo(false)}
                  className="h-6 w-6 p-0"
                >
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Route Summary */}
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <Navigation className="w-4 h-4 text-blue-600" />
                  <span>{selectedRoute.total_distance_nm.toFixed(1)} nm</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-green-600" />
                  <span>{selectedRoute.total_time_hours.toFixed(1)}h</span>
                </div>
                <div className="flex items-center gap-2">
                  <Fuel className="w-4 h-4 text-orange-600" />
                  <span>{selectedRoute.total_fuel_mt.toFixed(1)} MT</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-purple-600" />
                  <span>{(selectedRoute.safety_score * 100).toFixed(0)}%</span>
                </div>
              </div>

              {/* Safety Score */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>Safety Score</span>
                  <Badge 
                    variant={selectedRoute.safety_score >= 0.7 ? "default" : "destructive"}
                  >
                    {(selectedRoute.safety_score * 100).toFixed(0)}%
                  </Badge>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${selectedRoute.safety_score * 100}%`,
                      backgroundColor: getRouteColor(selectedRoute.safety_score)
                    }}
                  />
                </div>
              </div>

              {/* Weather Warnings */}
              {selectedRoute.weather_warnings.length > 0 && (
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm font-medium text-orange-600">
                    <AlertTriangle className="w-4 h-4" />
                    Weather Warnings
                  </div>
                  <div className="text-xs space-y-1">
                    {selectedRoute.weather_warnings.map((warning, index) => (
                      <div key={index} className="text-orange-700 bg-orange-50 p-2 rounded">
                        {warning}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Route Actions */}
              <div className="flex gap-2 pt-2">
                <Button size="sm" className="flex-1">
                  <Compass className="w-4 h-4 mr-2" />
                  Navigate
                </Button>
                <Button size="sm" variant="outline">
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
          <span>🌊 Marine Navigation System</span>
          <span>📍 {viewState.latitude.toFixed(2)}°N, {viewState.longitude.toFixed(2)}°E</span>
          <span>🔍 Zoom: {viewState.zoom.toFixed(1)}x</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            System Online
          </span>
          <span className="flex items-center gap-1">
            <Ship className="w-3 h-3" />
            {vesselPositions.length} Vessels
          </span>
          <span className="flex items-center gap-1">
            <Route className="w-3 h-3" />
            {routes.length} Routes
          </span>
        </div>
      </div>
    </div>
  );
}
