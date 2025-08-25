'use client';

import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';

// Fix for default markers in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Enhanced Professional Maritime Icons with better graphics
const createShipIcon = (isActive: boolean = false) => new L.DivIcon({
  html: `
    <div class="ship-marker ${isActive ? 'active' : ''}">
      <div class="ship-body">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="shipGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#1e40af"/>
              <stop offset="100%" style="stop-color:#3b82f6"/>
            </linearGradient>
            <filter id="dropShadow">
              <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="black" flood-opacity="0.3"/>
            </filter>
          </defs>
          <!-- Ship Hull -->
          <path d="M16 3L6 10v8l10 8 10-8v-8L16 3z" fill="url(#shipGradient)" stroke="#ffffff" stroke-width="2" filter="url(#dropShadow)"/>
          <!-- Ship Deck -->
          <ellipse cx="16" cy="16" rx="8" ry="4" fill="#1e40af" opacity="0.8"/>
          <!-- Navigation Light -->
          <circle cx="16" cy="16" r="4" fill="#ef4444" stroke="#ffffff" stroke-width="1"/>
          <circle cx="16" cy="16" r="2" fill="#ffffff" opacity="0.9"/>
          <!-- Ship Wake (when active) -->
          ${isActive ? `<path d="M16 26 Q12 24 8 26 Q12 28 16 26 Q20 28 24 26 Q20 24 16 26" fill="#3b82f6" opacity="0.3"/>` : ''}
        </svg>
      </div>
      ${isActive ? `<div class="radar-pulse"></div>` : ''}
    </div>
  `,
  className: 'custom-ship-icon enhanced',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const createPortIcon = (size: 'major' | 'minor' = 'minor', type: 'cargo' | 'container' | 'oil' = 'cargo') => new L.DivIcon({
  html: `
    <div class="port-marker ${size} ${type}">
      <div class="port-body">
        <svg width="${size === 'major' ? 36 : 24}" height="${size === 'major' ? 36 : 24}" viewBox="0 0 36 36" fill="none">
          <defs>
            <linearGradient id="portGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#059669"/>
              <stop offset="100%" style="stop-color:#10b981"/>
            </linearGradient>
          </defs>
          <!-- Port Base -->
          <circle cx="18" cy="18" r="16" fill="url(#portGradient)" stroke="#ffffff" stroke-width="2"/>
          <!-- Port Infrastructure -->
          <rect x="12" y="10" width="12" height="8" fill="#059669" rx="1"/>
          <rect x="14" y="12" width="8" height="4" fill="#34d399" rx="0.5"/>
          <!-- Cranes -->
          <line x1="10" y1="8" x2="26" y2="8" stroke="#374151" stroke-width="2"/>
          <line x1="12" y1="8" x2="12" y2="20" stroke="#374151" stroke-width="1.5"/>
          <line x1="24" y1="8" x2="24" y2="20" stroke="#374151" stroke-width="1.5"/>
          <!-- Containers -->
          <rect x="15" y="20" width="6" height="3" fill="#f59e0b" rx="0.5"/>
          <rect x="16" y="23" width="4" height="2" fill="#ef4444" rx="0.5"/>
        </svg>
      </div>
      <div class="port-name">${type.toUpperCase()}</div>
    </div>
  `,
  className: `custom-port-icon enhanced ${type}`,
  iconSize: [size === 'major' ? 36 : 24, size === 'major' ? 36 : 24],
  iconAnchor: [size === 'major' ? 18 : 12, size === 'major' ? 18 : 12],
});

const createWeatherIcon = (condition: string, temperature: number) => new L.DivIcon({
  html: `
    <div class="weather-marker">
      <div class="weather-body">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <defs>
            <linearGradient id="weatherGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#f59e0b"/>
              <stop offset="100%" style="stop-color:#f97316"/>
            </linearGradient>
          </defs>
          <circle cx="14" cy="14" r="12" fill="url(#weatherGradient)" stroke="#ffffff" stroke-width="2"/>
          <text x="14" y="18" text-anchor="middle" fill="white" font-size="10" font-weight="bold">${temperature}°</text>
        </svg>
      </div>
      <div class="weather-condition">${condition}</div>
    </div>
  `,
  className: 'custom-weather-icon enhanced',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const waypointIcon = new L.DivIcon({
  html: `
    <div class="waypoint-marker">
      <div class="waypoint-body">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6" fill="#3b82f6" stroke="#ffffff" stroke-width="2"/>
          <circle cx="8" cy="8" r="3" fill="#ffffff" opacity="0.8"/>
        </svg>
      </div>
    </div>
  `,
  className: 'custom-waypoint-icon enhanced',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

interface MapComponentProps {
  currentPosition?: { lat: number; lng: number } | null;
  route?: Array<{ lat: number; lng: number }>;
  ports?: Array<{ lat: number; lng: number; name: string }>;
  isTracking?: boolean;
  center?: [number, number];
  zoom?: number;
  weatherData?: { temperature: number; condition: string };
  originCity?: { name: string; lat: number; lng: number } | null;
  destinationCity?: { name: string; lat: number; lng: number } | null;
  routeDetails?: {
    vessel_type?: string;
    route_type?: string;
    routing_details?: any;
  };
}

// Enhanced Component to handle map updates and animations
function MapController({ currentPosition, center, isTracking }: { 
  currentPosition?: { lat: number; lng: number } | null, 
  center?: [number, number],
  isTracking?: boolean 
}) {
  const map = useMap();
  
  useEffect(() => {
    if (currentPosition) {
      map.setView([currentPosition.lat, currentPosition.lng], Math.max(map.getZoom(), 10), {
        animate: true,
        duration: 1.5
      });
    } else if (center) {
      map.setView(center, map.getZoom(), {
        animate: true,
        duration: 1.0
      });
    }
  }, [currentPosition, center, map]);

  useEffect(() => {
    if (isTracking) {
      const interval = setInterval(() => {
        map.invalidateSize();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isTracking, map]);

  return null;
}

// Enhanced Maritime Map with Better UX and Graphics
export default function EnhancedMaritimeMap({
  currentPosition,
  route = [],
  ports = [],
  isTracking = false,
  center = [25.0, 55.0],
  zoom = 3,
  weatherData,
  originCity,
  destinationCity,
  routeDetails
}: MapComponentProps) {
  const mapRef = useRef<L.Map>(null);

  // Enhanced tile layers with multiple options
  const tileLayerConfigs = [
    {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attribution: '© Esri, Maxar, Earthstar Geographics',
      name: 'Satellite'
    },
    {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: '© OpenStreetMap contributors',
      name: 'Streets'
    },
    {
      url: "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg",
      attribution: '© Stamen Design, © OpenStreetMap contributors',
      name: 'Artistic'
    }
  ];

  const selectedTileLayer = tileLayerConfigs[0]; // Default to satellite

  // Enhanced route visualization with animated polylines
  const routePolylineOptions = {
    color: '#3b82f6',
    weight: 4,
    opacity: 0.8,
    dashArray: isTracking ? '10, 5' : undefined,
    className: isTracking ? 'animated-route' : 'static-route'
  };

  return (
    <div className="relative w-full h-96 rounded-lg overflow-hidden shadow-2xl">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        zoomControl={true}
        className="w-full h-full maritime-map-container"
        ref={mapRef}
      >
        {/* Enhanced Satellite Imagery Layer */}
        <TileLayer
          url={selectedTileLayer.url}
          attribution={selectedTileLayer.attribution}
          maxZoom={18}
          tileSize={256}
        />

        {/* Map Controller for animations */}
        <MapController 
          currentPosition={currentPosition} 
          center={center} 
          isTracking={isTracking} 
        />

        {/* Enhanced Origin City Marker */}
        {originCity && (
          <Marker
            position={[originCity.lat, originCity.lng]}
            icon={createPortIcon('major', 'cargo')}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2 text-green-600">🚢 ORIGIN</h3>
                <h4 className="font-semibold text-base mb-1">{originCity.name}</h4>
                <p className="text-sm text-gray-600">
                  {originCity.lat.toFixed(4)}°N, {originCity.lng.toFixed(4)}°E
                </p>
                <div className="mt-2 p-2 bg-green-50 rounded text-xs">
                  <p className="text-green-700 font-medium">Departure Point</p>
                  {routeDetails?.vessel_type && (
                    <p className="text-green-600">Vessel: {routeDetails.vessel_type}</p>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Enhanced Destination City Marker */}
        {destinationCity && (
          <Marker
            position={[destinationCity.lat, destinationCity.lng]}
            icon={createPortIcon('major', 'container')}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2 text-blue-600">🎯 DESTINATION</h3>
                <h4 className="font-semibold text-base mb-1">{destinationCity.name}</h4>
                <p className="text-sm text-gray-600">
                  {destinationCity.lat.toFixed(4)}°N, {destinationCity.lng.toFixed(4)}°E
                </p>
                <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                  <p className="text-blue-700 font-medium">Arrival Port</p>
                  {routeDetails?.route_type && (
                    <p className="text-blue-600">Route: {routeDetails.route_type.replace('_', ' ')}</p>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Enhanced Ship Position Marker */}
        {currentPosition && (
          <Marker
            position={[currentPosition.lat, currentPosition.lng]}
            icon={createShipIcon(isTracking)}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2">🚢 Your Vessel</h3>
                <p className="mb-1">
                  <strong>Position:</strong><br />
                  {currentPosition.lat.toFixed(4)}°N, {currentPosition.lng.toFixed(4)}°E
                </p>
                {isTracking && (
                  <div className="mt-2 text-green-200">
                    <p className="text-sm">🟢 LIVE TRACKING ACTIVE</p>
                  </div>
                )}
                {weatherData && (
                  <div className="mt-2">
                    <p className="text-sm">
                      🌡️ {weatherData.temperature}°C - {weatherData.condition}
                    </p>
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Enhanced Route Visualization */}
        {route.length > 0 && (
          <>
            <Polyline
              positions={route.map(point => [point.lat, point.lng])}
              pathOptions={routePolylineOptions}
            />
            
            {/* Enhanced Waypoint Markers */}
            {route.map((point, index) => (
              <Marker
                key={`waypoint-${index}`}
                position={[point.lat, point.lng]}
                icon={waypointIcon}
              >
                <Popup>
                  <div className="text-center">
                    <h3 className="font-bold">📍 Waypoint {index + 1}</h3>
                    <p className="text-sm">
                      {point.lat.toFixed(4)}°, {point.lng.toFixed(4)}°
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}
          </>
        )}

        {/* Enhanced Port Markers */}
        {ports.map((port, index) => (
          <Marker
            key={`port-${index}`}
            position={[port.lat, port.lng]}
            icon={createPortIcon('major', 'container')}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2">🏗️ {port.name}</h3>
                <p className="mb-1">
                  <strong>Type:</strong> Container Port
                </p>
                <p className="text-sm">
                  {port.lat.toFixed(4)}°, {port.lng.toFixed(4)}°
                </p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Enhanced Weather Data Overlay */}
        {weatherData && currentPosition && (
          <Marker
            position={[currentPosition.lat + 0.1, currentPosition.lng + 0.1]}
            icon={createWeatherIcon(weatherData.condition, weatherData.temperature)}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2">🌤️ Weather Conditions</h3>
                <p className="mb-1">
                  <strong>Temperature:</strong> {weatherData.temperature}°C
                </p>
                <p className="mb-1">
                  <strong>Condition:</strong> {weatherData.condition}
                </p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Enhanced Coverage Radius for Tracking */}
        {currentPosition && isTracking && (
          <Circle
            center={[currentPosition.lat, currentPosition.lng]}
            radius={5000}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.1,
              weight: 2,
              dashArray: '5, 5'
            }}
          />
        )}
      </MapContainer>
    </div>
  );
}
