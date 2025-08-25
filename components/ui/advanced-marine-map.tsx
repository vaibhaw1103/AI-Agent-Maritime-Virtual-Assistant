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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Ship, 
  Anchor, 
  Waves, 
  Wind, 
  Compass, 
  Navigation,
  Thermometer,
  AlertTriangle,
  MapPin,
  Route,
  Clock,
  Fuel
} from 'lucide-react';

// Types for marine data
interface MarineWeatherData {
  timestamp: string;
  location: string;
  coordinates: [number, number];
  atmospheric: {
    temperature: number;
    humidity: number;
    pressure: number;
    visibility: number;
  };
  wind: {
    speed: number;
    direction: number;
    gust: number;
  };
  marine: {
    wave_height: number;
    wave_direction: number;
    wave_period: number;
    swell_height: number;
    swell_direction: number;
    swell_period: number;
    sea_state: string;
    sea_temperature: number;
  };
  currents: {
    speed: number;
    direction: number;
  };
  tides: {
    height: number;
    direction: string;
    next_high_tide: string;
    next_low_tide: string;
  };
  warnings: string[];
  storm_warnings: string[];
  source: string;
  confidence: number;
}

interface VesselTrack {
  vessel: {
    imo: string;
    mmsi: string;
    name: string;
    callsign: string;
    type: string;
    flag: string;
    gross_tonnage?: number;
    length?: number;
    width?: number;
    draft?: number;
  };
  current_position: {
    timestamp: string;
    latitude: number;
    longitude: number;
    speed: number;
    heading: number;
    course: number;
    status: string;
    source: string;
  };
  position_history: Array<{
    timestamp: string;
    latitude: number;
    longitude: number;
    speed: number;
    heading: number;
    status: string;
  }>;
  destination?: string;
  eta?: string;
  route_points?: [number, number][];
  weather_conditions?: any;
  alerts: string[];
}

interface RouteSegment {
  start: [number, number];
  end: [number, number];
  distance_nm: number;
  estimated_time_hours: number;
  fuel_consumption_mt: number;
  hazards: string[];
  depth_restrictions?: number;
  current_effects?: any;
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

interface AdvancedMarineMapProps {
  weatherData?: MarineWeatherData;
  vesselTracks?: VesselTrack[];
  optimizedRoute?: OptimizedRoute;
  showWeatherOverlays?: boolean;
  showVesselTracks?: boolean;
  showRouteOptimization?: boolean;
  onMapClick?: (coordinates: [number, number]) => void;
  onVesselClick?: (vessel: VesselTrack) => void;
  onRouteSegmentClick?: (segment: RouteSegment) => void;
}

const MAPBOX_ACCESS_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || 'your-mapbox-token-here';

export default function AdvancedMarineMap({
  weatherData,
  vesselTracks = [],
  optimizedRoute,
  showWeatherOverlays = true,
  showVesselTracks = true,
  showRouteOptimization = true,
  onMapClick,
  onVesselClick,
  onRouteSegmentClick
}: AdvancedMarineMapProps) {
  const [viewState, setViewState] = useState({
    longitude: -4.4777,
    latitude: 51.9244,
    zoom: 8
  });
  
  const [selectedVessel, setSelectedVessel] = useState<VesselTrack | null>(null);
  const [selectedRouteSegment, setSelectedRouteSegment] = useState<RouteSegment | null>(null);
  const [weatherLayer, setWeatherLayer] = useState<'wind' | 'waves' | 'currents' | 'none'>('none');
  const [mapStyle, setMapStyle] = useState<'satellite' | 'streets' | 'marine'>('marine');

  // Map styles
  const mapStyles = {
    satellite: 'mapbox://styles/mapbox/satellite-v9',
    streets: 'mapbox://styles/mapbox/streets-v12',
    marine: 'mapbox://styles/mapbox/navigation-night-v1'
  };

  // Weather overlay layers
  const weatherLayers = {
    wind: {
      id: 'wind-layer',
      type: 'symbol' as const,
      layout: {
        'icon-image': 'wind-arrow',
        'icon-size': 0.5,
        'icon-rotate': ['get', 'direction'],
        'icon-allow-overlap': true
      },
      paint: {
        'icon-color': [
          'interpolate',
          ['linear'],
          ['get', 'speed'],
          0, '#00ff00',
          10, '#ffff00',
          20, '#ff8000',
          30, '#ff0000'
        ]
      }
    },
    waves: {
      id: 'waves-layer',
      type: 'fill' as const,
      paint: {
        'fill-color': [
          'interpolate',
          ['linear'],
          ['get', 'height'],
          0, '#0000ff',
          2, '#0080ff',
          4, '#00ffff',
          6, '#ffff00',
          8, '#ff8000',
          10, '#ff0000'
        ],
        'fill-opacity': 0.6
      }
    },
    currents: {
      id: 'currents-layer',
      type: 'line' as const,
      paint: {
        'line-color': [
          'interpolate',
          ['linear'],
          ['get', 'speed'],
          0, '#0000ff',
          1, '#0080ff',
          2, '#00ffff',
          3, '#ffff00',
          4, '#ff8000',
          5, '#ff0000'
        ],
        'line-width': [
          'interpolate',
          ['linear'],
          ['get', 'speed'],
          0, 1,
          5, 5
        ]
      }
    }
  };

  // Handle map click
  const handleMapClick = useCallback((event: any) => {
    const coordinates: [number, number] = [event.lngLat.lng, event.lngLat.lat];
    onMapClick?.(coordinates);
  }, [onMapClick]);

  // Handle vessel click
  const handleVesselClick = useCallback((vessel: VesselTrack) => {
    setSelectedVessel(vessel);
    onVesselClick?.(vessel);
  }, [onVesselClick]);

  // Handle route segment click
  const handleRouteSegmentClick = useCallback((segment: RouteSegment) => {
    setSelectedRouteSegment(segment);
    onRouteSegmentClick?.(segment);
  }, [onRouteSegmentClick]);

  // Generate weather overlay data
  const generateWeatherOverlayData = useCallback(() => {
    if (!weatherData || weatherLayer === 'none') return null;

    const { coordinates } = weatherData;
    
    switch (weatherLayer) {
      case 'wind':
        return {
          type: 'FeatureCollection',
          features: [{
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: coordinates
            },
            properties: {
              speed: weatherData.wind.speed,
              direction: weatherData.wind.direction
            }
          }]
        };
      
      case 'waves':
        return {
          type: 'FeatureCollection',
          features: [{
            type: 'Feature',
            geometry: {
              type: 'Polygon',
              coordinates: [[
                [coordinates[0] - 0.1, coordinates[1] - 0.1],
                [coordinates[0] + 0.1, coordinates[1] - 0.1],
                [coordinates[0] + 0.1, coordinates[1] + 0.1],
                [coordinates[0] - 0.1, coordinates[1] + 0.1],
                [coordinates[0] - 0.1, coordinates[1] - 0.1]
              ]]
            },
            properties: {
              height: weatherData.marine.wave_height
            }
          }]
        };
      
      case 'currents':
        return {
          type: 'FeatureCollection',
          features: [{
            type: 'Feature',
            geometry: {
              type: 'LineString',
              coordinates: [
                coordinates,
                [
                  coordinates[0] + Math.cos(weatherData.currents.direction * Math.PI / 180) * 0.1,
                  coordinates[1] + Math.sin(weatherData.currents.direction * Math.PI / 180) * 0.1
                ]
              ]
            },
            properties: {
              speed: weatherData.currents.speed
            }
          }]
        };
      
      default:
        return null;
    }
  }, [weatherData, weatherLayer]);

  // Generate vessel track data
  const generateVesselTrackData = useCallback(() => {
    if (!showVesselTracks || vesselTracks.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: vesselTracks.map(vessel => ({
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: vessel.position_history.map(pos => [pos.longitude, pos.latitude])
        },
        properties: {
          vesselId: vessel.vessel.imo,
          vesselName: vessel.vessel.name,
          vesselType: vessel.vessel.type
        }
      }))
    };
  }, [vesselTracks, showVesselTracks]);

  // Generate route data
  const generateRouteData = useCallback(() => {
    if (!showRouteOptimization || !optimizedRoute) return null;

    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: optimizedRoute.waypoints
          },
          properties: {
            routeType: 'main',
            distance: optimizedRoute.total_distance_nm,
            time: optimizedRoute.total_time_hours,
            fuel: optimizedRoute.total_fuel_mt
          }
        },
        ...optimizedRoute.alternative_routes.map((route, index) => ({
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: route
          },
          properties: {
            routeType: 'alternative',
            index: index
          }
        }))
      ]
    };
  }, [optimizedRoute, showRouteOptimization]);

  const weatherOverlayData = generateWeatherOverlayData();
  const vesselTrackData = generateVesselTrackData();
  const routeData = generateRouteData();

  return (
    <div className="w-full h-full relative">
      <Map
        {...viewState}
        onMove={(evt: any) => setViewState(evt.viewState)}
        onClick={handleMapClick}
        mapStyle={mapStyles[mapStyle]}
        mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
        style={{ width: '100%', height: '100%' }}
        attributionControl={true}
      >
        <NavigationControl position="top-left" />
        <FullscreenControl position="top-right" />
        
        {/* Weather Overlay Source and Layer */}
        {weatherOverlayData && weatherLayer !== 'none' && (
          <Source id="weather-overlay" type="geojson" data={weatherOverlayData}>
            <Layer {...(weatherLayers[weatherLayer] as any)} />
          </Source>
        )}
        
        {/* Vessel Track Source and Layer */}
        {vesselTrackData && (
          <Source id="vessel-tracks" type="geojson" data={vesselTrackData}>
            <Layer
              id="vessel-tracks-line"
              type="line"
              paint={{
                'line-color': '#00ff00',
                'line-width': 2,
                'line-opacity': 0.8
              }}
            />
          </Source>
        )}
        
        {/* Route Source and Layer */}
        {routeData && (
          <Source id="route-data" type="geojson" data={routeData}>
            <Layer
              id="route-line"
              type="line"
              paint={{
                'line-color': [
                  'case',
                  ['==', ['get', 'routeType'], 'main'], '#ff0000',
                  '#00ff00'
                ],
                'line-width': [
                  'case',
                  ['==', ['get', 'routeType'], 'main'], 4,
                  2
                ],
                'line-opacity': 0.8
              }}
            />
          </Source>
        )}
        
        {/* Vessel Markers */}
        {showVesselTracks && vesselTracks.map(vessel => (
          <Marker
            key={vessel.vessel.imo}
            longitude={vessel.current_position.longitude}
            latitude={vessel.current_position.latitude}
            anchor="center"
            onClick={() => handleVesselClick(vessel)}
          >
            <div className="relative">
              <Ship 
                className="w-6 h-6 text-blue-600 cursor-pointer transform transition-transform hover:scale-110"
                style={{
                  transform: `rotate(${vessel.current_position.heading}deg)`
                }}
              />
              {vessel.alerts.length > 0 && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              )}
            </div>
          </Marker>
        ))}
        
        {/* Route Waypoint Markers */}
        {showRouteOptimization && optimizedRoute && optimizedRoute.waypoints.map((waypoint, index) => (
          <Marker
            key={`waypoint-${index}`}
            longitude={waypoint[0]}
            latitude={waypoint[1]}
            anchor="center"
          >
            <div className="relative">
              <MapPin className="w-5 h-5 text-red-500" />
              {index === 0 && (
                <Badge className="absolute -top-2 -left-2 text-xs">Start</Badge>
              )}
              {index === optimizedRoute.waypoints.length - 1 && (
                <Badge className="absolute -top-2 -left-2 text-xs">End</Badge>
              )}
            </div>
          </Marker>
        ))}
        
        {/* Vessel Popup */}
        {selectedVessel && (
          <Popup
            longitude={selectedVessel.current_position.longitude}
            latitude={selectedVessel.current_position.latitude}
            anchor="bottom"
            onClose={() => setSelectedVessel(null)}
            className="marine-vessel-popup"
          >
            <Card className="w-80">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Ship className="h-5 w-5" />
                  {selectedVessel.vessel.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="font-semibold">IMO:</span> {selectedVessel.vessel.imo}
                  </div>
                  <div>
                    <span className="font-semibold">MMSI:</span> {selectedVessel.vessel.mmsi}
                  </div>
                  <div>
                    <span className="font-semibold">Type:</span> {selectedVessel.vessel.type}
                  </div>
                  <div>
                    <span className="font-semibold">Flag:</span> {selectedVessel.vessel.flag}
                  </div>
                </div>
                
                <div className="border-t pt-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Navigation className="h-4 w-4" />
                    <span className="font-semibold">Current Position</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="font-semibold">Speed:</span> {selectedVessel.current_position.speed} kts
                    </div>
                    <div>
                      <span className="font-semibold">Heading:</span> {selectedVessel.current_position.heading}°
                    </div>
                    <div>
                      <span className="font-semibold">Status:</span> {selectedVessel.current_position.status}
                    </div>
                    <div>
                      <span className="font-semibold">Updated:</span> {new Date(selectedVessel.current_position.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                
                {selectedVessel.destination && (
                  <div className="border-t pt-2">
                    <div className="flex items-center gap-2 mb-2">
                      <Anchor className="h-4 w-4" />
                      <span className="font-semibold">Destination</span>
                    </div>
                    <div className="text-sm">
                      <div><span className="font-semibold">Port:</span> {selectedVessel.destination}</div>
                      {selectedVessel.eta && (
                        <div><span className="font-semibold">ETA:</span> {new Date(selectedVessel.eta).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                )}
                
                {selectedVessel.alerts.length > 0 && (
                  <div className="border-t pt-2">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <span className="font-semibold text-red-500">Alerts</span>
                    </div>
                    <div className="space-y-1">
                      {selectedVessel.alerts.map((alert, index) => (
                        <Badge key={index} variant="destructive" className="text-xs">
                          {alert}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </Popup>
        )}
        
        {/* Route Segment Popup */}
        {selectedRouteSegment && (
          <Popup
            longitude={(selectedRouteSegment.start[0] + selectedRouteSegment.end[0]) / 2}
            latitude={(selectedRouteSegment.start[1] + selectedRouteSegment.end[1]) / 2}
            anchor="bottom"
            onClose={() => setSelectedRouteSegment(null)}
          >
            <Card className="w-72">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Route className="h-5 w-5" />
                  Route Segment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-1">
                    <Navigation className="h-4 w-4" />
                    <span className="font-semibold">Distance:</span> {selectedRouteSegment.distance_nm.toFixed(1)} nm
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    <span className="font-semibold">Time:</span> {selectedRouteSegment.estimated_time_hours.toFixed(1)}h
                  </div>
                  <div className="flex items-center gap-1">
                    <Fuel className="h-4 w-4" />
                    <span className="font-semibold">Fuel:</span> {selectedRouteSegment.fuel_consumption_mt.toFixed(1)} MT
                  </div>
                  {selectedRouteSegment.depth_restrictions && (
                    <div className="flex items-center gap-1">
                      <Anchor className="h-4 w-4" />
                      <span className="font-semibold">Depth:</span> {selectedRouteSegment.depth_restrictions}m
                    </div>
                  )}
                </div>
                
                {selectedRouteSegment.hazards.length > 0 && (
                  <div className="border-t pt-2">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-orange-500" />
                      <span className="font-semibold text-orange-500">Hazards</span>
                    </div>
                    <div className="space-y-1">
                      {selectedRouteSegment.hazards.map((hazard, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {hazard}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </Popup>
        )}
      </Map>
      
      {/* Map Controls */}
      <div className="absolute top-4 right-4 space-y-2">
        <Card className="w-64">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Map Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Map Style Selector */}
            <div>
              <label className="text-xs font-medium mb-1 block">Map Style</label>
              <select
                value={mapStyle}
                onChange={(e) => setMapStyle(e.target.value as any)}
                className="w-full text-xs p-1 border rounded"
              >
                <option value="marine">Marine Navigation</option>
                <option value="satellite">Satellite</option>
                <option value="streets">Streets</option>
              </select>
            </div>
            
            {/* Weather Overlay Selector */}
            {showWeatherOverlays && (
              <div>
                <label className="text-xs font-medium mb-1 block">Weather Overlay</label>
                <select
                  value={weatherLayer}
                  onChange={(e) => setWeatherLayer(e.target.value as any)}
                  className="w-full text-xs p-1 border rounded"
                >
                  <option value="none">None</option>
                  <option value="wind">Wind</option>
                  <option value="waves">Waves</option>
                  <option value="currents">Currents</option>
                </select>
              </div>
            )}
            
            {/* Weather Data Display */}
            {weatherData && weatherLayer !== 'none' && (
              <div className="border-t pt-2">
                <div className="text-xs font-medium mb-2">Current Weather</div>
                <div className="grid grid-cols-2 gap-1 text-xs">
                  <div className="flex items-center gap-1">
                    <Thermometer className="h-3 w-3" />
                    {weatherData.atmospheric.temperature}°C
                  </div>
                  <div className="flex items-center gap-1">
                    <Wind className="h-3 w-3" />
                    {weatherData.wind.speed} m/s
                  </div>
                  <div className="flex items-center gap-1">
                    <Waves className="h-3 w-3" />
                    {weatherData.marine.wave_height}m
                  </div>
                  <div className="flex items-center gap-1">
                    <Compass className="h-3 w-3" />
                    {weatherData.wind.direction}°
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Route Information Panel */}
      {showRouteOptimization && optimizedRoute && (
        <div className="absolute bottom-4 left-4">
          <Card className="w-80">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Route className="h-4 w-4" />
                Optimized Route
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 bg-blue-500 text-white rounded">
                  <div className="text-lg font-bold">{optimizedRoute.total_distance_nm.toFixed(0)}</div>
                  <div className="text-xs">Nautical Miles</div>
                </div>
                <div className="p-2 bg-green-500 text-white rounded">
                  <div className="text-lg font-bold">{optimizedRoute.total_time_hours.toFixed(0)}h</div>
                  <div className="text-xs">Transit Time</div>
                </div>
                <div className="p-2 bg-orange-500 text-white rounded">
                  <div className="text-lg font-bold">{optimizedRoute.total_fuel_mt.toFixed(0)}</div>
                  <div className="text-xs">Fuel (MT)</div>
                </div>
              </div>
              
              <div className="text-xs">
                <div><span className="font-semibold">Optimization:</span> {optimizedRoute.optimization_mode}</div>
                <div><span className="font-semibold">Route Type:</span> {optimizedRoute.route_type}</div>
                <div><span className="font-semibold">Safety Score:</span> {optimizedRoute.safety_score.toFixed(0)}%</div>
                <div><span className="font-semibold">ETA:</span> {new Date(optimizedRoute.estimated_arrival).toLocaleString()}</div>
              </div>
              
              {optimizedRoute.weather_warnings.length > 0 && (
                <div className="border-t pt-2">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    <span className="text-xs font-semibold text-red-500">Weather Warnings</span>
                  </div>
                  <div className="space-y-1">
                    {optimizedRoute.weather_warnings.map((warning, index) => (
                      <Badge key={index} variant="destructive" className="text-xs">
                        {warning}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
