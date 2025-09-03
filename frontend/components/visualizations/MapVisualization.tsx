'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { MapData } from '@/types/api';

// Dynamically import Plot to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface MapVisualizationProps {
  data: MapData;
  summary: string;
}

export function MapVisualization({ data, summary }: MapVisualizationProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-600">Loading map visualization...</div>
      </div>
    );
  }

  const plotData = [{
    type: 'scattermapbox' as const,
    lat: data.latitudes,
    lon: data.longitudes,
    mode: 'markers' as const,
    marker: {
      size: 8,
      color: '#3B82F6',
      opacity: 0.8,
    },
    text: data.labels,
    hovertemplate: '<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>',
  }];

  const layout = {
    mapbox: {
      style: 'open-street-map',
      center: {
        lat: data.latitudes.reduce((a, b) => a + b, 0) / data.latitudes.length,
        lon: data.longitudes.reduce((a, b) => a + b, 0) / data.longitudes.length,
      },
      zoom: 3,
    },
    margin: { l: 0, r: 0, t: 0, b: 0 },
    height: 400,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
  };

  const config = {
    displayModeBar: false,
    responsive: true,
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <Plot
          data={plotData}
          layout={layout}
          config={config}
          style={{ width: '100%' }}
        />
      </div>
      
      <div className="text-sm text-gray-700 leading-relaxed">
        {summary}
      </div>
    </div>
  );
}