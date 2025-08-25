'use client';

import React, { useState, useEffect, useRef, Suspense, lazy } from 'react';
// --- Component Imports ---
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
// --- Icon Imports ---
import { 
  Loader2, 
  Search, 
  MapPin, 
  Navigation, 
  Ship,
  Anchor,
  AlertTriangle,
  Satellite,
  Waves,
  Route,
  Clock,
  Compass,
  Thermometer,
  Wind
} from "lucide-react";

// --- API Client Import ---
import { maritimeAPI, getPortWeather, LocationResult, VesselResult, RouteResult } from '@/lib/api/client';

// --- Map Component ---
const ProfessionalMapLibreMap = lazy(() => 
  import('@/components/ui/professional-maplibre-map').catch(() => ({
      default: () => (
          <div className="w-full h-96 rounded-lg bg-gray-200 flex items-center justify-center border">
              <p className="text-gray-500 font-semibold">Professional MapLibre Map Component Failed to Load</p>
          </div>
      )
  }))
);

export default function WeatherPage() {
  // --- State Declarations ---
  const [vesselQuery, setVesselQuery] = useState<string>('');
  const [vessels, setVessels] = useState<VesselResult[]>([]);
  const [vesselLoading, setVesselLoading] = useState<boolean>(false);
  
  const [routeFrom, setRouteFrom] = useState<string>('');
  const [routeTo, setRouteTo] = useState<string>('');
  const [routeResult, setRouteResult] = useState<RouteResult | null>(null);
  const [routeLoading, setRouteLoading] = useState<boolean>(false);
  const [originCity, setOriginCity] = useState<{name: string, lat: number, lng: number} | null>(null);
  const [destinationCity, setDestinationCity] = useState<{name: string, lat: number, lng: number} | null>(null);
  const [optimizationMode, setOptimizationMode] = useState<'time' | 'fuel' | 'weather'>('weather');
  const [fromSuggestions, setFromSuggestions] = useState<LocationResult[]>([]);
  const [toSuggestions, setToSuggestions] = useState<LocationResult[]>([]);
  const [fromSearchLoading, setFromSearchLoading] = useState(false);
  const [toSearchLoading, setToSearchLoading] = useState(false);
  const fromDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const toDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const [selectedOriginOverride, setSelectedOriginOverride] = useState<{name: string; lat: number; lng: number} | null>(null);
  const [selectedDestOverride, setSelectedDestOverride] = useState<{name: string; lat: number; lng: number} | null>(null);
  
  const [portWeatherQuery, setPortWeatherQuery] = useState<string>('');
  const [portWeatherData, setPortWeatherData] = useState<any>(null);
  const [portWeatherLoading, setPortWeatherLoading] = useState<boolean>(false);

  const [isRouteTracking, setIsRouteTracking] = useState<boolean>(false);
  const [currentPosition, setCurrentPosition] = useState<{lat: number, lng: number} | null>(null);
  const [trackingInterval, setTrackingInterval] = useState<NodeJS.Timeout | null>(null);
  
  const [searchError, setSearchError] = useState('');

  // --- API Handlers ---

  const getWeatherForPortHandler = async () => {
    if (!portWeatherQuery.trim()) return;
    
    setPortWeatherLoading(true);
    setSearchError('');
    try {
      const response = await getPortWeather(portWeatherQuery);
      setPortWeatherData(response);
    } catch (error) {
      console.error('Port weather search failed:', error);
      setSearchError(`Could not retrieve weather for port: ${portWeatherQuery}`);
      setPortWeatherData(null);
    } finally {
      setPortWeatherLoading(false);
    }
  };

  const trackVesselsHandler = async () => {
    if (!vesselQuery.trim()) {
      setSearchError('Please enter a vessel name or IMO number');
      return;
    }
    
    setVesselLoading(true);
    setSearchError('');
    setVessels([]); // Clear previous results
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      const results = await maritimeAPI.trackVessels({
        vessel_name: vesselQuery.trim(),
        include_weather: true,
        include_route: true
      });
      
      clearTimeout(timeoutId);
      
      if (!results || results.length === 0) {
        setSearchError('No vessels found matching your search criteria');
        return;
      }
      
      setVessels(results);
    } catch (error) {
      console.error('Vessel tracking failed:', error);
      setSearchError(
        error instanceof Error && error.name === 'AbortError' 
          ? 'Request timed out. Please try again.'
          : error instanceof Error 
            ? error.message 
            : 'An error occurred while tracking the vessel'
      );
    } finally {
      setVesselLoading(false);
    }
  };

  const getCoordinatesForLocation = async (query: string): Promise<{name: string, lat: number, lng: number} | null> => {
    if (!query) return null;
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
      if (!response.ok) throw new Error('Nominatim API request failed');
      const data = await response.json();
      if (data && data.length > 0) {
        return { name: data[0].display_name, lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
      }
      return null;
    } catch (error) {
      console.error('Failed to get coordinates:', error);
      return null;
    }
  };

  const optimizeRouteHandler = async () => {
    if (!routeFrom.trim() || !routeTo.trim()) {
      setSearchError('Please enter both origin and destination');
      return;
    }
    
    setRouteLoading(true);
    setSearchError('');
    setRouteResult(null);
    
    try {
      const originCoords = selectedOriginOverride ?? await getCoordinatesForLocation(routeFrom.trim());
      const destCoords = selectedDestOverride ?? await getCoordinatesForLocation(routeTo.trim());
      
      if (!originCoords || !destCoords) {
        setSearchError('Could not find coordinates for one or both locations. Please be more specific.');
        return;
      }
      
      setOriginCity({ name: routeFrom.trim(), lat: originCoords.lat, lng: originCoords.lng });
      setDestinationCity({ name: routeTo.trim(), lat: destCoords.lat, lng: destCoords.lng });
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      const result = await maritimeAPI.optimizeRoute({
        origin: { lat: originCoords.lat, lng: originCoords.lng },
        destination: { lat: destCoords.lat, lng: destCoords.lng },
        optimization: optimizationMode,
        include_weather: true,
        include_hazards: true
      });
      
      clearTimeout(timeoutId);
      setRouteResult(result);

    } catch (error) {
      console.error('Route optimization failed:', error);
      if (!searchError) {
        setSearchError(
          error instanceof Error && error.name === 'AbortError'
            ? 'Request timed out. Please try again.'
            : error instanceof Error
              ? error.message
              : 'Failed to optimize route. The API might be unavailable.'
        );
      }
    } finally {
      setRouteLoading(false);
    }
  };

  const searchPortsHandler = async (query: string, which: 'from' | 'to') => {
    if (!query || query.trim().length < 3) {
      if (which === 'from') setFromSuggestions([]); else setToSuggestions([]);
      return;
    }
    
    const setLoading = which === 'from' ? setFromSearchLoading : setToSearchLoading;
    const setSuggestions = which === 'from' ? setFromSuggestions : setToSuggestions;

    setLoading(true);
    try {
      const response = await fetch(`/api/ports/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Port search failed');
      const data = await response.json();
      setSuggestions(data);
    } catch (e) {
      console.error('Port search failed', e);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const reOptimizeRouteRealTime = async (currentPos: {lat: number, lng: number}) => {
    if (!destinationCity) return;
    
    try {
        const response = await fetch('/api/routes/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                origin: currentPos,
                destination: { lat: destinationCity.lat, lng: destinationCity.lng },
                optimization: optimizationMode,
            }),
        });
        if (!response.ok) throw new Error('Real-time re-optimization failed');
        const result = await response.json();
      
        setRouteResult(result);
        setOriginCity({ name: "Current Position", lat: currentPos.lat, lng: currentPos.lng });
    } catch (error) {
      console.error('Real-time route optimization failed:', error);
      setSearchError('Live re-optimization failed.');
    }
  };

  const startRealTimeTracking = () => {
    if (isRouteTracking || !routeResult) return;
    
    setIsRouteTracking(true);
    setSearchError('');
    
    const interval = setInterval(() => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const newPos = { lat: position.coords.latitude, lng: position.coords.longitude };
            setCurrentPosition(newPos);
            reOptimizeRouteRealTime(newPos);
          },
          (error) => {
            console.error('GPS error:', error);
            setSearchError('GPS signal lost. Cannot update route.');
            stopRealTimeTracking();
          }
        );
      } else {
        setSearchError('Geolocation is not supported by this browser.');
        stopRealTimeTracking();
      }
    }, 30000);
    
    setTrackingInterval(interval);
  };

  const stopRealTimeTracking = () => {
    setIsRouteTracking(false);
    if (trackingInterval) {
      clearInterval(trackingInterval);
      setTrackingInterval(null);
    }
  };

  useEffect(() => {
    return () => {
      if (trackingInterval) clearInterval(trackingInterval);
    };
  }, [trackingInterval]);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Waves className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold">Maritime Operations Center</h1>
        </div>
        {/* Back to Dashboard Button */}
        <a href="/" className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition font-semibold shadow">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          Back to Dashboard
        </a>
      </div>
      
      {searchError && (
        <Card className="bg-red-50 border-red-200 text-red-700">
            <CardContent className="pt-4 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                <p className="font-medium">{searchError}</p>
            </CardContent>
        </Card>
      )}

      <Tabs defaultValue="routes" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="routes">Route Optimization</TabsTrigger>
          <TabsTrigger value="ports">Port Weather</TabsTrigger>
          <TabsTrigger value="vessels">Vessel Tracking</TabsTrigger>
        </TabsList>
        
        <TabsContent value="ports" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Anchor className="h-5 w-5" />
                Maritime Port Weather
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input 
                  placeholder="Enter port name (e.g., singapore, rotterdam, shanghai)"
                  value={portWeatherQuery}
                  onChange={(e) => setPortWeatherQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && getWeatherForPortHandler()}
                />
                <Button 
                  onClick={getWeatherForPortHandler}
                  disabled={portWeatherLoading || !portWeatherQuery.trim()}
                >
                  {portWeatherLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                </Button>
              </div>

              {portWeatherData && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Waves className="h-5 w-5" />
                      Port of {portWeatherQuery.charAt(0).toUpperCase() + portWeatherQuery.slice(1).replace("-", " ")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                      <div className="text-center">
                        <Thermometer className="h-8 w-8 mx-auto text-orange-500 mb-2" />
                        <div className="text-2xl font-bold">{portWeatherData.current_weather.temperature}°C</div>
                        <div className="text-sm text-muted-foreground">Temperature</div>
                      </div>
                      <div className="text-center">
                        <Wind className="h-8 w-8 mx-auto text-gray-500 mb-2" />
                        <div className="text-2xl font-bold">{portWeatherData.current_weather.wind_speed} m/s</div>
                        <div className="text-sm text-muted-foreground">Wind Speed</div>
                      </div>
                      <div className="text-center">
                        <Waves className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                        <div className="text-2xl font-bold">{portWeatherData.marine_conditions.wave_height} m</div>
                        <div className="text-sm text-muted-foreground">Wave Height</div>
                      </div>
                      <div className="text-center">
                        <Compass className="h-8 w-8 mx-auto text-green-500 mb-2" />
                        <div className="text-2xl font-bold">{portWeatherData.marine_conditions.sea_state}</div>
                        <div className="text-sm text-muted-foreground">Sea State</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="vessels" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ship className="h-5 w-5" />
                Vessel Tracking
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Enter vessel name, IMO, or MMSI..."
                  value={vesselQuery}
                  onChange={(e) => setVesselQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && trackVesselsHandler()}
                />
                <Button onClick={trackVesselsHandler} disabled={vesselLoading}>
                  {vesselLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Track"}
                </Button>
              </div>

              {vessels.length > 0 && (
                <div className="space-y-2">
                  {vessels.map((vessel, index) => (
                    <Card key={index}>
                      <CardContent className="pt-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold">{vessel.name}</h4>
                            <p className="text-sm text-muted-foreground">IMO: {vessel.imo} | Type: {vessel.type}</p>
                            <p className="text-xs text-muted-foreground">{vessel.lat.toFixed(4)}, {vessel.lng.toFixed(4)}</p>
                          </div>
                          <div className="text-right">
                            <Badge>{vessel.status}</Badge>
                            <p className="text-sm mt-1">{vessel.speed} kts</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="routes" className="space-y-4">
          {isRouteTracking && (
            <Card className="bg-gradient-to-r from-green-500 to-blue-500 text-white border-none">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Satellite className="h-6 w-6 animate-pulse" />
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full animate-ping"></div>
                    </div>
                    <div>
                      <h3 className="font-bold">🔴 LIVE TRACKING ACTIVE</h3>
                      <p className="text-sm opacity-90">Route optimizing in real-time based on GPS position.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Route className="h-5 w-5" />
                Route Optimization
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative">
                  <Label>From</Label>
                  <Input
                    placeholder="Origin port or city..."
                    value={routeFrom}
                    onChange={(e) => {
                      const v = e.target.value; setRouteFrom(v); setSelectedOriginOverride(null);
                      if (fromDebounceRef.current) clearTimeout(fromDebounceRef.current);
                      fromDebounceRef.current = setTimeout(() => searchPortsHandler(v, 'from'), 500);
                    }}
                  />
                  {fromSearchLoading && <Loader2 className="absolute right-2 top-9 h-4 w-4 animate-spin text-muted-foreground" />}
                  {fromSuggestions.length > 0 && (
                    <div className="absolute z-20 mt-1 w-full rounded-md border bg-background shadow-lg max-h-60 overflow-y-auto">
                      {fromSuggestions.map((s, idx) => (
                        <button
                          key={`from-sugg-${idx}`}
                          className="w-full text-left px-3 py-2 hover:bg-accent hover:text-accent-foreground border-b last:border-b-0"
                          onClick={() => {
                            setRouteFrom(s.name.split(',')[0]);
                            setSelectedOriginOverride({ name: s.name, lat: s.lat, lng: s.lng });
                            setFromSuggestions([]);
                          }}
                        >
                          <div className="text-sm font-medium flex items-center gap-2"><MapPin className="h-4 w-4 text-muted-foreground"/> {s.name}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="relative">
                  <Label>To</Label>
                  <Input
                    placeholder="Destination port or city..."
                    value={routeTo}
                    onChange={(e) => {
                      const v = e.target.value; setRouteTo(v); setSelectedDestOverride(null);
                      if (toDebounceRef.current) clearTimeout(toDebounceRef.current);
                      toDebounceRef.current = setTimeout(() => searchPortsHandler(v, 'to'), 500);
                    }}
                  />
                  {toSearchLoading && <Loader2 className="absolute right-2 top-9 h-4 w-4 animate-spin text-muted-foreground" />}
                  {toSuggestions.length > 0 && (
                    <div className="absolute z-20 mt-1 w-full rounded-md border bg-background shadow-lg max-h-60 overflow-y-auto">
                      {toSuggestions.map((s, idx) => (
                        <button
                          key={`to-sugg-${idx}`}
                          className="w-full text-left px-3 py-2 hover:bg-accent hover:text-accent-foreground border-b last:border-b-0"
                          onClick={() => {
                            setRouteTo(s.name.split(',')[0]);
                            setSelectedDestOverride({ name: s.name, lat: s.lat, lng: s.lng });
                            setToSuggestions([]);
                          }}
                        >
                          <div className="text-sm font-medium flex items-center gap-2"><MapPin className="h-4 w-4 text-muted-foreground"/> {s.name}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div>
                  <Label>Optimization</Label>
                  <Select value={optimizationMode} onValueChange={(v) => setOptimizationMode(v as 'time' | 'fuel' | 'weather')}>
                    <SelectTrigger><SelectValue placeholder="Select optimization" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="time">Fastest time</SelectItem>
                      <SelectItem value="fuel">Lowest fuel</SelectItem>
                      <SelectItem value="weather">Weather-aware</SelectItem>
                    </SelectContent>
                  </Select>
              </div>

              <div className="flex gap-2">
                <Button onClick={optimizeRouteHandler} disabled={routeLoading}>
                  {routeLoading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin"/> Optimizing...</> : "Optimize Route"}
                </Button>
                <Button onClick={startRealTimeTracking} variant="outline" disabled={!routeResult}>
                  <Clock className="h-4 w-4 mr-2" />
                  Start Live Tracking
                </Button>
              </div>

              {routeResult && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Navigation className="h-5 w-5" />
                      Optimized Maritime Route
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Suspense fallback={
                        <div className="w-full h-96 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                            <div className="text-center text-white">
                                <Satellite className="h-12 w-12 mx-auto mb-4 animate-spin" />
                                <p>Loading Enhanced Maritime Map...</p>
                            </div>
                        </div>
                    }>
                        <ProfessionalMapLibreMap
                            routes={routeResult ? [{
                                origin: [originCity?.lat || 0, originCity?.lng || 0] as [number, number],
                                destination: [destinationCity?.lat || 0, destinationCity?.lng || 0] as [number, number],
                                waypoints: routeResult.route_points.map(point => [point.lat, point.lng] as [number, number]),
                                segments: [],
                                total_distance_nm: routeResult.distance_nm,
                                total_time_hours: routeResult.estimated_time_hours,
                                total_fuel_mt: routeResult.fuel_consumption_mt,
                                optimization_mode: optimizationMode,
                                weather_warnings: [],
                                safety_score: 0.85,
                                route_type: "marine_optimized",
                                estimated_arrival: new Date(Date.now() + routeResult.estimated_time_hours * 60 * 60 * 1000).toISOString(),
                                alternative_routes: []
                            }] : []}
                            weatherData={portWeatherData ? {
                                wind_speed: portWeatherData.wind?.speed || 0,
                                wind_direction: portWeatherData.wind?.direction || 0,
                                wave_height: portWeatherData.waves?.height || 0,
                                temperature: portWeatherData.temperature || 0,
                                visibility: portWeatherData.visibility || 0,
                                pressure: portWeatherData.pressure || 0,
                                storm_warnings: portWeatherData.warnings || []
                            } : undefined}
                            vesselPositions={vessels.map(vessel => ({
                                id: vessel.imo,
                                position: [vessel.lat, vessel.lng] as [number, number],
                                heading: vessel.heading || 0,
                                speed: vessel.speed || 0,
                                vessel_type: vessel.type || 'Unknown'
                            }))}
                            onRouteSelect={(route) => {
                                console.log('Selected route:', route);
                            }}
                            className="w-full h-96"
                        />
                    </Suspense>
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-center">
                          <div className="text-lg font-bold">{routeResult.distance_nm}</div>
                          <div className="text-xs opacity-90">Nautical Miles</div>
                        </div>
                        <div className="p-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg text-center">
                          <div className="text-lg font-bold">{routeResult.estimated_time_hours}h</div>
                          <div className="text-xs opacity-90">Transit Time</div>
                        </div>
                        <div className="p-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg text-center">
                          <div className="text-lg font-bold">{routeResult.fuel_consumption_mt}</div>
                          <div className="text-xs opacity-90">Fuel (MT)</div>
                        </div>
                        <div className="p-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg text-center">
                          <div className="text-lg font-bold">{routeResult.route_points.length}</div>
                          <div className="text-xs opacity-90">Waypoints</div>
                        </div>
                      </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
