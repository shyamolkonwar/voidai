"use client";

import * as React from 'react';
import Map, { Marker, MapRef } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapCardProps {
  lat: number;
  lng: number;
  zoom?: number;
  points?: { lat: number; lng: number; summary: any }[];
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

export default function MapCard({ lat, lng, zoom = 12, points }: MapCardProps) {
  const [error, setError] = React.useState<string | null>(null);
  const mapRef = React.useRef<MapRef>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  if (!MAPBOX_TOKEN) {
    console.error('Mapbox token is missing');
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline"> Mapbox token is not configured. Please set the NEXT_PUBLIC_MAPBOX_TOKEN environment variable.</span>
      </div>
    );
  }

  const handleMapLoad = (event: any) => {
    setError(null);
  };

  const handleMapError = (event: any) => {
    setError(`Map error: ${event.error?.message || 'Unknown error'}`);
  };

  const handleWebGLContextLost = (event: any) => {
    console.error('=== WEBGL CONTEXT LOST ===');
    console.error('WebGL context lost:', event);
    setError('WebGL context lost - map cannot render');
  };

  return (
    <div className="relative w-full" style={{ height: '400px', minHeight: '400px', maxHeight: '400px' }}>
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-100 z-10">
          <div className="text-red-600 font-semibold p-4 text-center">
            <div className="text-lg mb-2">🗺️ Map Error</div>
            <div>{error}</div>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Reload Map
            </button>
          </div>
        </div>
      )}
      
      <div ref={containerRef} className="w-full h-full overflow-hidden" style={{ height: '400px', minHeight: '400px' }}>
        <Map
          ref={mapRef}
          initialViewState={{
            latitude: lat,
            longitude: lng,
            zoom: zoom,
          }}
          style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, zIndex: 1 }}
          mapStyle="mapbox://styles/mapbox/streets-v11"
          mapboxAccessToken={MAPBOX_TOKEN}
          onLoad={handleMapLoad}
          onError={handleMapError}
        >
          <Marker longitude={lng} latitude={lat} color="#3B82F6" />
          {points && points.map((point, index) => (
            <Marker key={index} longitude={point.lng} latitude={point.lat} color="#EF4444" />
          ))}
        </Map>
      </div>
    </div>
  );
}
