'use client';

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix for default markers in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const SimpleMapTest: React.FC = () => {
  return (
    <div style={{ 
      width: '100%', 
      height: '500px', 
      border: '2px solid red',
      backgroundColor: 'lightblue',
      position: 'relative'
    }}>
      <h3 style={{ 
        color: 'black', 
        margin: '10px',
        position: 'absolute',
        top: '0',
        left: '0',
        zIndex: 1000,
        backgroundColor: 'yellow',
        padding: '5px'
      }}>
        Simple Map Test - Container Visible
      </h3>
      <div style={{ width: '100%', height: '100%', marginTop: '40px' }}>
        <MapContainer
          center={[51.505, -0.09]}
          zoom={13}
          style={{ 
            height: '100%', 
            width: '100%',
            minHeight: '400px'
          }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[51.505, -0.09]}>
            <Popup>
              TEST MARKER - Map is working!
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  );
};

export default SimpleMapTest;
