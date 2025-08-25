'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
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
  Route,
  Globe,
  Eye,
  EyeOff
} from 'lucide-react';

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

interface ProfessionalMapLibreMapProps {
  routes?: OptimizedRoute[];
  weatherData?: MarineWeatherData;
  vesselPositions?: VesselPosition[];
  onRouteSelect?: (route: OptimizedRoute) => void;
  className?: string;
}

// Professional marine map styles
const MARINE_MAP_STYLES = {
  nautical: {
    version: 8,
    glyphs: "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
    sources: {
      'osm': {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      },
      'maritime': {
        type: 'raster',
        tiles: ['https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenSeaMap'
      }
    },
    layers: [
      {
        id: 'osm-tiles',
        type: 'raster',
        source: 'osm',
        paint: {
          'raster-opacity': 0.8
        }
      },
      {
        id: 'maritime-overlay',
        type: 'raster',
        source: 'maritime',
        paint: {
          'raster-opacity': 0.6
        }
      }
    ]
  },
  satellite: {
    version: 8,
    glyphs: "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
    sources: {
      'satellite': {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: '© Esri'
      }
    },
    layers: [
      {
        id: 'satellite-tiles',
        type: 'raster',
        source: 'satellite'
      }
    ]
  },
  dark: {
    version: 8,
    glyphs: "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
    sources: {
      'osm': {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      }
    },
    layers: [
      {
        id: 'osm-tiles',
        type: 'raster',
        source: 'osm',
        paint: {
          'raster-opacity': 0.7,
          'raster-brightness-min': 0.3,
          'raster-saturation': 0.5
        }
      }
    ]
  }
};

export default function ProfessionalMapLibreMap({
  routes = [],
  weatherData,
  vesselPositions = [],
  onRouteSelect,
  className = "w-full h-full"
}: ProfessionalMapLibreMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapStyle, setMapStyle] = useState('nautical');
  const [activeLayers, setActiveLayers] = useState({
    bathymetry: true,
    weather: true,
    vessels: true,
    routes: true,
    waypoints: true
  });
  const [selectedRoute, setSelectedRoute] = useState<OptimizedRoute | null>(null);
  const [showRouteInfo, setShowRouteInfo] = useState(false);
  const [center, setCenter] = useState<[number, number]>([30, 0]);
  const [zoom, setZoom] = useState(2);

  // Initialize map
  useEffect(() => {
    if (mapContainer.current && !map.current) {
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: MARINE_MAP_STYLES.nautical as any,
        center: center,
        zoom: zoom,
        attributionControl: false,
        logoPosition: 'bottom-right'
      });

      // Add navigation controls
      map.current.addControl(new maplibregl.NavigationControl(), 'top-left');
      map.current.addControl(new maplibregl.FullscreenControl(), 'top-left');

      // Add custom attribution
      map.current.addControl(new maplibregl.AttributionControl({
        compact: true,
        customAttribution: '© OpenStreetMap, © OpenSeaMap'
      }), 'bottom-left');

      // Map event listeners
      map.current.on('move', () => {
        if (map.current) {
          setCenter(map.current.getCenter().toArray() as [number, number]);
          setZoom(map.current.getZoom());
        }
      });

      // Add custom marine styling
      map.current.on('load', () => {
        if (map.current) {
          // Add ocean water styling
          map.current.addSource('ocean', {
            type: 'geojson',
            data: {
              type: 'Feature',
              geometry: {
                type: 'Polygon',
                coordinates: [[
                  [-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]
                ]]
              }
            }
          });

          map.current.addLayer({
            id: 'ocean-fill',
            type: 'fill',
            source: 'ocean',
            paint: {
              'fill-color': '#1e3a8a',
              'fill-opacity': 0.1
            }
          }, 'osm-tiles');
        }
      });
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update map style
  useEffect(() => {
    if (map.current && MARINE_MAP_STYLES[mapStyle as keyof typeof MARINE_MAP_STYLES]) {
      map.current.setStyle(MARINE_MAP_STYLES[mapStyle as keyof typeof MARINE_MAP_STYLES] as any);
    }
  }, [mapStyle]);

  // Update routes
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    // Remove existing route layers
    if (map.current.getLayer('routes')) map.current.removeLayer('routes');
    if (map.current.getSource('routes')) map.current.removeSource('routes');

    if (routes.length > 0) {
      // Create route GeoJSON
      const routeFeatures = routes.map((route, index) => ({
        type: 'Feature' as const,
        properties: {
          id: index,
          safety_score: route.safety_score,
          distance: route.total_distance_nm,
          time: route.total_time_hours,
          mode: route.optimization_mode
        },
        geometry: {
          type: 'LineString' as const,
          coordinates: [
            [route.origin[1], route.origin[0]],
            ...route.waypoints.map(wp => [wp[1], wp[0]]),
            [route.destination[1], route.destination[0]]
          ].filter(coord => coord[0] !== 0 && coord[1] !== 0)
        }
      }));

      const routeData = {
        type: 'FeatureCollection' as const,
        features: routeFeatures
      };

      // Add route source and layer
      map.current.addSource('routes', {
        type: 'geojson',
        data: routeData
      });

      map.current.addLayer({
        id: 'routes',
        type: 'line',
        source: 'routes',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': [
            'case',
            ['>=', ['get', 'safety_score'], 0.8], '#10b981',
            ['>=', ['get', 'safety_score'], 0.6], '#f59e0b',
            '#ef4444'
          ],
          'line-width': 6,
          'line-opacity': 0.8
        }
      });

      // Add route labels
      map.current.addLayer({
        id: 'route-labels',
        type: 'symbol',
        source: 'routes',
        layout: {
          'text-field': ['concat', 'Route ', ['get', 'id']],
          'text-font': ['Open Sans Regular'],
          'text-size': 12,
          'text-offset': [0, 0],
          'text-anchor': 'center'
        },
        paint: {
          'text-color': '#1f2937',
          'text-halo-color': '#ffffff',
          'text-halo-width': 2
        }
      });

      // Fit map to routes
      const bounds = new maplibregl.LngLatBounds();
      routeFeatures.forEach(feature => {
        feature.geometry.coordinates.forEach(coord => {
          bounds.extend(coord as [number, number]);
        });
      });
      map.current.fitBounds(bounds, { padding: 50 });
    }
  }, [routes, map.current]);

  // Update vessels
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    // Remove existing vessel layers
    if (map.current.getLayer('vessels')) map.current.removeLayer('vessels');
    if (map.current.getSource('vessels')) map.current.removeSource('vessels');

    if (vesselPositions.length > 0 && activeLayers.vessels) {
      const vesselFeatures = vesselPositions.map(vessel => ({
        type: 'Feature' as const,
        properties: {
          id: vessel.id,
          type: vessel.vessel_type,
          speed: vessel.speed,
          heading: vessel.heading
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [vessel.position[1], vessel.position[0]]
        }
      }));

      const vesselData = {
        type: 'FeatureCollection' as const,
        features: vesselFeatures
      };

      // Add vessel source and layer
      map.current.addSource('vessels', {
        type: 'geojson',
        data: vesselData
      });

      map.current.addLayer({
        id: 'vessels',
        type: 'symbol',
        source: 'vessels',
        layout: {
          'icon-image': 'ship-icon',
          'icon-size': 1.5,
          'icon-rotate': ['get', 'heading'],
          'icon-allow-overlap': true
        }
      });

      // Add custom ship icon
      const shipIcon = new Image();
      shipIcon.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIwIDIxVjNMMTMgMTBMMTAgN0w0IDEzVjIxSDBWMTlIMlYxNUw4IDIxSDE2TDIyIDE1VjE5SDI0VjIxSDIwWiIgZmlsbD0iIzFlNDBhZiIvPgo8L3N2Zz4K';
      shipIcon.onload = () => {
        if (map.current) {
          map.current.addImage('ship-icon', shipIcon);
        }
      };
    }
  }, [vesselPositions, activeLayers.vessels, map.current]);

  // Update weather overlay
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded() || !weatherData || !activeLayers.weather) return;

    // Remove existing weather layers
    if (map.current.getLayer('weather-overlay')) map.current.removeLayer('weather-overlay');
    if (map.current.getSource('weather-overlay')) map.current.removeSource('weather-overlay');

    // Create weather overlay
    const weatherFeature = {
      type: 'Feature' as const,
      properties: {
        wind_speed: weatherData.wind_speed,
        wave_height: weatherData.wave_height,
        temperature: weatherData.temperature
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [center[1], center[0]]
      }
    };

    const weatherData_ = {
      type: 'FeatureCollection' as const,
      features: [weatherFeature]
    };

    // Add weather source and layer
    map.current.addSource('weather-overlay', {
      type: 'geojson',
      data: weatherData_
    });

    map.current.addLayer({
      id: 'weather-overlay',
      type: 'circle',
      source: 'weather-overlay',
      paint: {
        'circle-radius': 100000,
        'circle-color': [
          'case',
          ['>', ['get', 'wind_speed'], 20], '#ef4444',
          ['>', ['get', 'wind_speed'], 10], '#f59e0b',
          '#10b981'
        ],
        'circle-opacity': 0.3,
        'circle-stroke-width': 2,
        'circle-stroke-color': [
          'case',
          ['>', ['get', 'wind_speed'], 20], '#dc2626',
          ['>', ['get', 'wind_speed'], 10], '#d97706',
          '#059669'
        ]
      }
    });
  }, [weatherData, activeLayers.weather, center, map.current]);

  const handleRouteClick = (route: OptimizedRoute) => {
    setSelectedRoute(route);
    setShowRouteInfo(true);
    onRouteSelect?.(route);
  };

  const getRouteColor = (safetyScore: number) => {
    if (safetyScore >= 0.8) return '#10b981';
    if (safetyScore >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className={`${className} relative bg-gray-900 rounded-lg overflow-hidden`}>
      {/* Map Container */}
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Map Controls Panel */}
      <div className="absolute top-4 right-4 space-y-2">
        <Card className="w-64 bg-white/95 backdrop-blur-sm shadow-lg">
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
                <Anchor className="w-4 h-4" />
                Bathymetry
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.weather}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, weather: e.target.checked }))}
                  className="rounded"
                />
                <Wind className="w-4 h-4" />
                Weather
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.vessels}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, vessels: e.target.checked }))}
                  className="rounded"
                />
                <Ship className="w-4 h-4" />
                Vessels
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={activeLayers.routes}
                  onChange={(e) => setActiveLayers(prev => ({ ...prev, routes: e.target.checked }))}
                  className="rounded"
                />
                <Route className="w-4 h-4" />
                Routes
              </label>
            </div>
            
            <div className="pt-2 border-t">
              <label className="text-sm font-medium flex items-center gap-2">
                <Globe className="w-4 h-4" />
                Map Style:
              </label>
              <select
                value={mapStyle}
                onChange={(e) => setMapStyle(e.target.value)}
                className="w-full mt-1 p-2 border rounded text-sm bg-white"
              >
                <option value="nautical">🌊 Nautical</option>
                <option value="satellite">🛰️ Satellite</option>
                <option value="dark">🌙 Dark</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Route Information Panel */}
      {showRouteInfo && selectedRoute && (
        <div className="absolute bottom-4 left-4 w-80">
          <Card className="bg-white/95 backdrop-blur-sm shadow-lg">
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
          <span>🌊 Professional Marine Map</span>
          <span>📍 {center[0].toFixed(2)}°, {center[1].toFixed(2)}°</span>
          <span>🔍 Zoom: {zoom.toFixed(1)}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-green-400" />
            MapLibre GL
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
