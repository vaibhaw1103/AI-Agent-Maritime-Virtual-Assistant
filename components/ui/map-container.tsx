'use client';

import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fix for default markers in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom ship icon
const shipIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <path fill="#1e40af" d="M16 2L4 14h24L16 2z"/>
      <path fill="#3b82f6" d="M4 14v4l12 8 12-8v-4H4z"/>
      <circle fill="#ef4444" cx="16" cy="16" r="3"/>
    </svg>
  `),
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

// Port icon
const portIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <circle fill="#059669" cx="12" cy="12" r="8"/>
      <circle fill="#ffffff" cx="12" cy="12" r="4"/>
      <text x="12" y="16" text-anchor="middle" font-size="8" fill="#059669">P</text>
    </svg>
  `),
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

interface MapComponentProps {
  currentPosition?: { lat: number; lng: number };
  route?: Array<{ lat: number; lng: number }>;
  ports?: Array<{ lat: number; lng: number; name: string }>;
  isTracking?: boolean;
  center?: [number, number];
  zoom?: number;
}

// Component to handle map updates
function MapUpdater({ currentPosition, center }: { currentPosition?: { lat: number; lng: number }, center?: [number, number] }) {
  const map = useMap();
  
  useEffect(() => {
    if (currentPosition) {
      map.setView([currentPosition.lat, currentPosition.lng], 8);
    } else if (center) {
      map.setView(center, 6);
    }
  }, [currentPosition, center, map]);
  
  return null;
}

export default function MapComponentInternal({
  currentPosition,
  route = [],
  ports = [],
  isTracking = false,
  center = [25.0, 55.0], // Default to Dubai area
  zoom = 4
}: MapComponentProps) {
  // Default ports to show
  const defaultPorts = ports.length > 0 ? ports : [
    { lat: 1.3521, lng: 103.8198, name: "Singapore" },
    { lat: 51.9244, lng: 4.4777, name: "Rotterdam" },
    { lat: 25.2582, lng: 55.3047, name: "Dubai" },
    { lat: 31.2304, lng: 121.4737, name: "Shanghai" },
    { lat: 53.5511, lng: 9.9937, name: "Hamburg" }
  ];

  return (
    <div className="w-full h-96 rounded-lg overflow-hidden border border-border">
      <MapContainer
        center={currentPosition ? [currentPosition.lat, currentPosition.lng] as L.LatLngTuple : center as L.LatLngTuple}
        zoom={currentPosition ? 8 : zoom}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapUpdater currentPosition={currentPosition} center={center} />

        {/* Current Position Marker */}
        {currentPosition && (
          <Marker position={[currentPosition.lat, currentPosition.lng] as L.LatLngTuple} icon={shipIcon}>
            <Popup>
              <div className="text-center">
                <strong>🚢 Current Position</strong>
                <br />
                <small>{currentPosition.lat.toFixed(4)}, {currentPosition.lng.toFixed(4)}</small>
                <br />
                {isTracking && (
                  <span className="text-green-600 font-medium">
                    📡 Live Tracking Active
                  </span>
                )}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Port Markers */}
        {defaultPorts.map((port, index) => (
          <Marker key={index} position={[port.lat, port.lng] as L.LatLngTuple} icon={portIcon}>
            <Popup>
              <div className="text-center">
                <strong>⚓ {port.name}</strong>
                <br />
                <small>{port.lat.toFixed(4)}, {port.lng.toFixed(4)}</small>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Route Line */}
        {route.length > 1 && (
          <Polyline
            positions={route.map(point => [point.lat, point.lng] as L.LatLngTuple)}
            pathOptions={{
              color: "#3b82f6",
              weight: 3,
              opacity: 0.8,
              dashArray: "10, 10"
            }}
          />
        )}
      </MapContainer>
    </div>
  );
}
