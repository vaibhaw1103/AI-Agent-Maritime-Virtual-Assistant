'use client';

import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

// Fix for default markers in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface HackathonMaritimeMapProps {
  routePoints: Array<{ lat: number; lng: number }>;
  vessels?: Array<{ lat: number; lng: number; name: string; status: string }>;
  weatherData?: Array<{ lat: number; lng: number; condition: string; temperature?: number }>;
  originCity?: { name: string; lat: number; lng: number } | null;
  destinationCity?: { name: string; lat: number; lng: number } | null;
  routeDetails?: {
    distance_nm?: number;
    estimated_time_hours?: number;
    fuel_consumption_mt?: number;
    route_type?: string;
  };
}

const HackathonMaritimeMap: React.FC<HackathonMaritimeMapProps> = ({ 
  routePoints, 
  vessels = [],
  weatherData = [],
  originCity, 
  destinationCity,
  routeDetails 
}) => {
  const mapRef = useRef<L.Map | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([25.0, 55.0]);
  const [mapZoom, setMapZoom] = useState(4);
  
  // Debug log
  console.log('HackathonMaritimeMap rendering with:', { 
    routePoints: routePoints?.length || 0, 
    weatherData: weatherData?.length || 0 
  });

  // Calculate optimal map view
  useEffect(() => {
    const allPoints: Array<{ lat: number; lng: number }> = [];
    
    if (routePoints && routePoints.length > 0) {
      allPoints.push(...routePoints);
    }
    
    if (originCity) allPoints.push(originCity);
    if (destinationCity) allPoints.push(destinationCity);

    if (allPoints.length > 0) {
      const lats = allPoints.map(p => p.lat);
      const lngs = allPoints.map(p => p.lng);
      const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
      const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
      setMapCenter([centerLat, centerLng]);
      setMapZoom(6);
    }
  }, [routePoints, originCity, destinationCity]);

  const routePositions: Array<[number, number]> = routePoints?.map(point => [point.lat, point.lng]) || [];

  return (
    <div style={{ width: '100%', height: '500px', border: '1px solid #ccc', position: 'relative' }}>
      {/* Debug indicator */}
      <div style={{
        position: 'absolute', 
        top: '10px', 
        left: '10px', 
        background: 'green', 
        color: 'white', 
        padding: '5px', 
        zIndex: 9999,
        fontSize: '12px'
      }}>
        MARITIME MAP LOADED - Routes: {routePoints?.length || 0}
      </div>

      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
        zoomControl={true}
        scrollWheelZoom={true}
      >
        {/* Base Layer - Using working OpenStreetMap */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={18}
        />
        {/* Nautical seamarks overlay for professional marine navigation visuals */}
        <TileLayer
          url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png"
          attribution='&copy; OpenSeaMap contributors'
          opacity={0.9}
          zIndex={500}
        />
        
        {/* Route Line */}
        {routePositions.length > 1 && (
          <Polyline
            positions={routePositions}
            color="#1e40af"
            weight={4}
            opacity={0.8}
          />
        )}
        
        {/* Origin Marker */}
        {originCity && (
          <Marker position={[originCity.lat, originCity.lng]}>
            <Popup>
              <div>
                <strong>Origin: {originCity.name}</strong>
                <br />
                Lat: {originCity.lat.toFixed(4)}
                <br />
                Lng: {originCity.lng.toFixed(4)}
              </div>
            </Popup>
          </Marker>
        )}
        
        {/* Destination Marker */}
        {destinationCity && (
          <Marker position={[destinationCity.lat, destinationCity.lng]}>
            <Popup>
              <div>
                <strong>Destination: {destinationCity.name}</strong>
                <br />
                Lat: {destinationCity.lat.toFixed(4)}
                <br />
                Lng: {destinationCity.lng.toFixed(4)}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Route waypoints */}
        {routePoints && routePoints.length > 2 && 
          routePoints.slice(1, -1).map((point, index) => (
            <Marker 
              key={`waypoint-${index}`} 
              position={[point.lat, point.lng]}
            >
              <Popup>
                <div>
                  <strong>Waypoint {index + 1}</strong>
                  <br />
                  Lat: {point.lat.toFixed(4)}
                  <br />
                  Lng: {point.lng.toFixed(4)}
                </div>
              </Popup>
            </Marker>
          ))
        }
      </MapContainer>

      {/* Route Information Panel */}
      {routeDetails && (
        <div style={{
          position: 'absolute',
          bottom: '10px',
          right: '10px',
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '8px',
          fontSize: '12px',
          zIndex: 1000
        }}>
          <div><strong>Route Details:</strong></div>
          <div>Distance: {routeDetails.distance_nm?.toFixed(1) || 'N/A'} nm</div>
          <div>Time: {routeDetails.estimated_time_hours?.toFixed(1) || 'N/A'} hrs</div>
          <div>Fuel: {routeDetails.fuel_consumption_mt?.toFixed(1) || 'N/A'} mt</div>
          <div>Type: {routeDetails.route_type || 'N/A'}</div>
        </div>
      )}
    </div>
  );
};

export default HackathonMaritimeMap;
