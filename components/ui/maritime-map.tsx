'use client';

import React from 'react';

interface Props {
  currentPosition?: { lat: number; lng: number } | null;
  route?: Array<{ lat: number; lng: number }>;
  ports?: Array<{ lat: number; lng: number; name: string }>;
}

export default function MaritimeMap({ currentPosition = null, route = [], ports = [] }: Props) {
  return (
    <div className="w-full h-96 rounded-lg border border-border flex items-center justify-center">
      <div className="text-center">
        <div className="text-lg font-bold">Maritime Map (placeholder)</div>
        <div className="text-sm text-muted-foreground">Vessels: {ports.length} • Waypoints: {route.length}</div>
      </div>
    </div>
  );
}
