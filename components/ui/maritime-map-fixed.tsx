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

// Enhanced Icons for Source and Destination
const createSourceIcon = () => new L.DivIcon({
  html: `
    <div class="source-marker" style="position: relative; z-index: 1000;">
      <div class="source-body" style="filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4)); transition: all 0.3s ease;">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="sourceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#10b981"/>
              <stop offset="100%" style="stop-color:#059669"/>
            </linearGradient>
            <filter id="sourceDropShadow">
              <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="black" flood-opacity="0.4"/>
            </filter>
          </defs>
          <circle cx="20" cy="20" r="18" fill="url(#sourceGradient)" stroke="#ffffff" stroke-width="3" filter="url(#sourceDropShadow)"/>
          <path d="M12 15L20 8L28 15v12l-8 6-8-6V15z" fill="#ffffff" stroke="#10b981" stroke-width="1.5"/>
          <circle cx="20" cy="20" r="4" fill="#10b981"/>
          <text x="20" y="25" text-anchor="middle" fill="white" font-size="8" font-weight="bold">START</text>
        </svg>
      </div>
      <div style="position: absolute; top: -8px; left: -8px; width: 56px; height: 56px; border: 3px solid #10b981; border-radius: 50%; animation: sourcePulse 2s infinite; pointer-events: none; opacity: 0.6;"></div>
    </div>
  `,
  className: 'custom-source-icon enhanced',
  iconSize: [40, 40],
  iconAnchor: [20, 20],
});

const createDestinationIcon = () => new L.DivIcon({
  html: `
    <div class="destination-marker" style="position: relative; z-index: 1000;">
      <div class="destination-body" style="filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4)); transition: all 0.3s ease;">
        <svg width="40" height="48" viewBox="0 0 40 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="destGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#ef4444"/>
              <stop offset="100%" style="stop-color:#dc2626"/>
            </linearGradient>
            <filter id="destDropShadow">
              <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="black" flood-opacity="0.4"/>
            </filter>
          </defs>
          <path d="M20 2C12.3 2 6 8.3 6 16c0 11.5 14 28 14 28s14-16.5 14-28c0-7.7-6.3-14-14-14z" fill="url(#destGradient)" stroke="#ffffff" stroke-width="3" filter="url(#destDropShadow)"/>
          <circle cx="20" cy="16" r="8" fill="#ffffff" stroke="#ef4444" stroke-width="2"/>
          <circle cx="20" cy="16" r="4" fill="#ef4444"/>
          <text x="20" y="35" text-anchor="middle" fill="white" font-size="7" font-weight="bold">DEST</text>
        </svg>
      </div>
      <div style="position: absolute; top: -8px; left: -8px; width: 56px; height: 56px; border: 3px solid #ef4444; border-radius: 50%; animation: destPulse 2.5s infinite; pointer-events: none; opacity: 0.6;"></div>
    </div>
  `,
  className: 'custom-destination-icon enhanced',
  iconSize: [40, 48],
  iconAnchor: [20, 44],
});

// Enhanced Professional Maritime Icons with better graphics
const createShipIcon = (isActive: boolean = false) => new L.DivIcon({
  html: `
    <div class="ship-marker ${isActive ? 'active' : ''}" style="position: relative; z-index: 1000;">
      <div class="ship-body" style="filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4)); transition: all 0.3s ease;">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="shipGradient${isActive ? 'Active' : ''}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#1e40af"/>
              <stop offset="100%" style="stop-color:#3b82f6"/>
            </linearGradient>
            <filter id="dropShadow${isActive ? 'Active' : ''}">
              <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="black" flood-opacity="0.3"/>
            </filter>
          </defs>
          <path d="M16 3L6 10v8l10 8 10-8v-8L16 3z" fill="url(#shipGradient${isActive ? 'Active' : ''})" stroke="#ffffff" stroke-width="2" filter="url(#dropShadow${isActive ? 'Active' : ''})"/>
          <ellipse cx="16" cy="16" rx="8" ry="4" fill="#1e40af" opacity="0.8"/>
          <circle cx="16" cy="16" r="4" fill="#ef4444" stroke="#ffffff" stroke-width="1"/>
          <circle cx="16" cy="16" r="2" fill="#ffffff" opacity="0.9"/>
          ${isActive ? `<path d="M16 26 Q12 24 8 26 Q12 28 16 26 Q20 28 24 26 Q20 24 16 26" fill="#3b82f6" opacity="0.3"/>` : ''}
        </svg>
      </div>
      ${isActive ? `<div style="position: absolute; top: -16px; left: -16px; width: 64px; height: 64px; border: 2px solid #ef4444; border-radius: 50%; animation: radarPulse 3s infinite; pointer-events: none;"></div>` : ''}
    </div>
  `,
  className: 'custom-ship-icon enhanced',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const createPortIcon = (size: 'major' | 'minor' = 'minor', type: 'cargo' | 'container' | 'oil' = 'cargo') => new L.DivIcon({
  html: `
    <div class="port-marker ${size} ${type}" style="position: relative; z-index: 900; ${size === 'major' ? 'transform: scale(1.2);' : ''}">
      <div class="port-body">
        <svg width="${size === 'major' ? 36 : 24}" height="${size === 'major' ? 36 : 24}" viewBox="0 0 36 36" fill="none">
          <defs>
            <linearGradient id="portGradient${size}${type}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#059669"/>
              <stop offset="100%" style="stop-color:#10b981"/>
            </linearGradient>
          </defs>
          <circle cx="18" cy="18" r="16" fill="url(#portGradient${size}${type})" stroke="#ffffff" stroke-width="2"/>
          <rect x="12" y="10" width="12" height="8" fill="#059669" rx="1"/>
          <rect x="14" y="12" width="8" height="4" fill="#34d399" rx="0.5"/>
          <line x1="10" y1="8" x2="26" y2="8" stroke="#374151" stroke-width="2"/>
          <line x1="12" y1="8" x2="12" y2="20" stroke="#374151" stroke-width="1.5"/>
          <line x1="24" y1="8" x2="24" y2="20" stroke="#374151" stroke-width="1.5"/>
          <rect x="15" y="20" width="6" height="3" fill="#f59e0b" rx="0.5"/>
          <rect x="16" y="23" width="4" height="2" fill="#ef4444" rx="0.5"/>
        </svg>
      </div>
      <div style="position: absolute; top: 100%; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; white-space: nowrap; opacity: 0; transition: opacity 0.3s ease;">${type.toUpperCase()}</div>
    </div>
  `,
  className: `custom-port-icon enhanced ${type}`,
  iconSize: [size === 'major' ? 36 : 24, size === 'major' ? 36 : 24],
  iconAnchor: [size === 'major' ? 18 : 12, size === 'major' ? 18 : 12],
});

const createWeatherIcon = (condition: string, temperature: number) => new L.DivIcon({
  html: `
    <div class="weather-marker" style="position: relative; z-index: 800;">
      <div class="weather-body">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <defs>
            <linearGradient id="weatherGradient${temperature}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#f59e0b"/>
              <stop offset="100%" style="stop-color:#f97316"/>
            </linearGradient>
          </defs>
          <circle cx="14" cy="14" r="12" fill="url(#weatherGradient${temperature})" stroke="#ffffff" stroke-width="2"/>
          <text x="14" y="18" text-anchor="middle" fill="white" font-size="10" font-weight="bold">${temperature}°</text>
        </svg>
      </div>
      <div style="position: absolute; top: 100%; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); color: white; padding: 2px 4px; border-radius: 3px; font-size: 8px; white-space: nowrap; opacity: 0; transition: opacity 0.3s ease;">${condition}</div>
    </div>
  `,
  className: 'custom-weather-icon enhanced',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const waypointIcon = new L.DivIcon({
  html: `
    <div class="waypoint-marker enhanced" style="position: relative; z-index: 700;">
      <div class="waypoint-body" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
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

// Fixed Maritime Map Component
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

  // Enhanced tile layers with multiple options for better graphics
  const tileLayerConfigs = [
    {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attribution: '© Esri, Maxar, Earthstar Geographics',
      name: 'Satellite'
    },
    {
      url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      attribution: '© CARTO © OpenStreetMap contributors',
      name: 'Navigation'
    },
    {
      url: "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
      attribution: '© OpenSeaMap contributors',
      name: 'Nautical'
    }
  ];

  const selectedTileLayer = tileLayerConfigs[0]; // Default to satellite
  const nauticalOverlay = tileLayerConfigs[2]; // Nautical overlay

  // Professional route visualization with multiple layers
  const mainRouteOptions = {
    color: '#1e40af',
    weight: 6,
    opacity: 0.9,
    lineCap: 'round' as const,
    lineJoin: 'round' as const
  };

  const routeGlowOptions = {
    color: '#3b82f6',
    weight: 12,
    opacity: 0.3,
    lineCap: 'round' as const,
    lineJoin: 'round' as const
  };

  const routeAnimationOptions = {
    color: '#60a5fa',
    weight: 3,
    opacity: 0.7,
    dashArray: '15, 10',
    lineCap: 'round' as const,
    lineJoin: 'round' as const,
    className: 'animated-maritime-route'
  };

  return (
    <div className="relative w-full h-96 rounded-lg overflow-hidden shadow-2xl">
      {/* Enhanced inline styles for professional maritime graphics */}
      <style jsx>{`
        @keyframes sourcePulse {
          0% { 
            opacity: 0.8;
            transform: scale(0.9);
            border-color: #10b981;
          }
          50% { 
            opacity: 0.4;
            transform: scale(1.2);
            border-color: #34d399;
          }
          100% { 
            opacity: 0.1;
            transform: scale(1.6);
            border-color: #6ee7b7;
          }
        }
        
        @keyframes destPulse {
          0% { 
            opacity: 0.8;
            transform: scale(0.9);
            border-color: #ef4444;
          }
          50% { 
            opacity: 0.4;
            transform: scale(1.2);
            border-color: #f87171;
          }
          100% { 
            opacity: 0.1;
            transform: scale(1.6);
            border-color: #fca5a5;
          }
        }
        
        @keyframes radarPulse {
          0% { 
            opacity: 1;
            transform: scale(0.5);
            border-color: #ef4444;
          }
          50% { 
            opacity: 0.5;
            transform: scale(1);
            border-color: #f87171;
          }
          100% { 
            opacity: 0;
            transform: scale(1.8);
            border-color: #fca5a5;
          }
        }
        
        @keyframes routeFlow {
          0% {
            stroke-dashoffset: 0;
          }
          100% {
            stroke-dashoffset: 50px;
          }
        }
        
        .leaflet-container {
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
          border-radius: 12px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        .leaflet-popup-content-wrapper {
          background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
          color: white;
          border-radius: 12px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
          border: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .leaflet-popup-content {
          margin: 16px 20px;
          line-height: 1.5;
          font-weight: 500;
        }
        
        .leaflet-popup-tip {
          background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
          border: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .popup-title {
          font-size: 16px;
          font-weight: 700;
          margin-bottom: 8px;
          color: #f8fafc;
        }
        
        .popup-text {
          font-size: 14px;
          margin-bottom: 4px;
          color: #e2e8f0;
        }
        
        .popup-coords {
          font-size: 12px;
          color: #cbd5e1;
          font-family: monospace;
        }
        
        .popup-status {
          font-size: 13px;
          color: #bfdbfe;
        }
        
        .animated-maritime-route {
          animation: routeFlow 3s linear infinite;
        }
        
        .source-marker:hover .source-body {
          transform: scale(1.1);
          filter: drop-shadow(0 8px 16px rgba(0,0,0,0.6));
        }
        
        .destination-marker:hover .destination-body {
          transform: scale(1.1);
          filter: drop-shadow(0 8px 16px rgba(0,0,0,0.6));
        }
        
        .ship-marker:hover .ship-body {
          transform: scale(1.15);
          filter: drop-shadow(0 6px 12px rgba(0,0,0,0.5));
        }
        
        .leaflet-control-container {
          filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
        }
        
        .leaflet-control-zoom a {
          background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
          color: white;
          border: none;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .leaflet-control-zoom a:hover {
          background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
          transform: scale(1.05);
        }
      `}</style>

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
            icon={createSourceIcon()}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2 text-green-200">🚢 DEPARTURE PORT</h3>
                <h4 className="font-semibold text-base mb-1 text-white">{originCity.name}</h4>
                <p className="text-sm text-gray-200">
                  {originCity.lat.toFixed(4)}°N, {originCity.lng.toFixed(4)}°E
                </p>
                <div className="mt-2 p-2 bg-green-900 bg-opacity-50 rounded text-xs">
                  <p className="text-green-200 font-medium">🟢 ORIGIN POINT</p>
                  {routeDetails?.vessel_type && (
                    <p className="text-green-300">Vessel: {routeDetails.vessel_type}</p>
                  )}
                  <p className="text-green-300 mt-1">Ready for departure</p>
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Enhanced Destination City Marker */}
        {destinationCity && (
          <Marker
            position={[destinationCity.lat, destinationCity.lng]}
            icon={createDestinationIcon()}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-bold text-lg mb-2 text-red-200">🎯 DESTINATION PORT</h3>
                <h4 className="font-semibold text-base mb-1 text-white">{destinationCity.name}</h4>
                <p className="text-sm text-gray-200">
                  {destinationCity.lat.toFixed(4)}°N, {destinationCity.lng.toFixed(4)}°E
                </p>
                <div className="mt-2 p-2 bg-red-900 bg-opacity-50 rounded text-xs">
                  <p className="text-red-200 font-medium">🔴 ARRIVAL PORT</p>
                  {routeDetails?.route_type && (
                    <p className="text-red-300">Route: {routeDetails.route_type.replace('_', ' ')}</p>
                  )}
                  <p className="text-red-300 mt-1">Awaiting vessel arrival</p>
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

        {/* Professional Multi-Layer Route Visualization */}
        {route.length > 0 && (
          <>
            {/* Route glow effect (bottom layer) */}
            <Polyline
              positions={route.map(point => [point.lat, point.lng])}
              pathOptions={routeGlowOptions}
            />
            
            {/* Main route line (middle layer) */}
            <Polyline
              positions={route.map(point => [point.lat, point.lng])}
              pathOptions={mainRouteOptions}
            />
            
            {/* Animated route overlay (top layer) */}
            <Polyline
              positions={route.map(point => [point.lat, point.lng])}
              pathOptions={routeAnimationOptions}
            />
            
            {/* Enhanced Waypoint Markers with proper spacing */}
            {route.filter((_, index) => index > 0 && index < route.length - 1 && index % 2 === 0).map((point, index) => (
              <Circle
                key={`waypoint-${index}`}
                center={[point.lat, point.lng]}
                radius={12000}
                pathOptions={{
                  color: '#1e40af',
                  weight: 2,
                  fillColor: '#3b82f6',
                  fillOpacity: 0.4,
                  className: 'waypoint-circle'
                }}
              />
            ))}
          </>
        )}

        {/* Nautical Chart Overlay */}
        <TileLayer
          url={nauticalOverlay.url}
          attribution={nauticalOverlay.attribution}
          maxZoom={16}
          opacity={0.25}
          className="nautical-overlay"
        />

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
