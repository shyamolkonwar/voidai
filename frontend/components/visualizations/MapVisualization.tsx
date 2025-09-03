'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { TableData } from '@/types/api';
import { TableVisualization } from './TableVisualization';

// Dynamically import Plot to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js') as any, { ssr: false });

interface MapVisualizationProps {
  data: TableData[];
  summary: string;
}

export function MapVisualization({ data, summary }: MapVisualizationProps) {
  const [isClient, setIsClient] = useState(false);
  const [plotData, setPlotData] = useState<any>(null);
  const [layout, setLayout] = useState<any>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (data && data.length > 0) {
      // Extract coordinates and prepare plot data
      const latitudes: number[] = [];
      const longitudes: number[] = [];
      const labels: string[] = [];

      data.forEach((row, index) => {
        if (row.latitude !== undefined && row.longitude !== undefined) {
          try {
            const lat = typeof row.latitude === 'string' ? parseFloat(row.latitude) : row.latitude;
            const lon = typeof row.longitude === 'string' ? parseFloat(row.longitude) : row.longitude;
            
            if (!isNaN(lat) && !isNaN(lon)) {
              latitudes.push(lat);
              longitudes.push(lon);
              
              // Create label from other fields
              const labelParts = Object.entries(row)
                .filter(([key]) => key !== 'latitude' && key !== 'longitude')
                .map(([key, value]) => `${key}: ${value}`)
                .slice(0, 3);
              
              labels.push(labelParts.join('<br>') || `Point ${index + 1}`);
            }
          } catch {
            // Skip invalid coordinates
          }
        }
      });

      if (latitudes.length > 0) {
        const plotDataConfig = [{
          type: 'scattermapbox',
          lat: latitudes,
          lon: longitudes,
          mode: 'markers',
          marker: {
            size: 12,
            color: '#3B82F6',
            opacity: 0.8,
          },
          text: labels,
          hovertemplate: '<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>',
        }];

        const layoutConfig = {
          mapbox: {
            style: 'open-street-map',
            center: {
              lat: latitudes.reduce((a: number, b: number) => a + b, 0) / latitudes.length,
              lon: longitudes.reduce((a: number, b: number) => a + b, 0) / longitudes.length,
            },
            zoom: 2,
          },
          margin: { l: 0, r: 0, t: 0, b: 0 },
          height: 400,
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
        };

        setPlotData(plotDataConfig);
        setLayout(layoutConfig);
      }
    }
  }, [data]);

  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-600">Loading map visualization...</div>
      </div>
    );
  }

  const hasValidData = plotData && plotData.length > 0;

  return (
    <div className="space-y-6">
      {/* Map Section */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Map View</h3>
        </div>
        {hasValidData ? (
          <div>
            {/* @ts-ignore */}
            <Plot
              data={plotData}
              layout={layout}
              config={{
                displayModeBar: false,
                responsive: true,
              }}
              style={{ width: '100%' }}
            />
          </div>
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500 text-center">
              <div className="text-lg mb-2">🌊</div>
              <p>No valid coordinate data found</p>
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-700 leading-relaxed">
        {summary}
      </div>

      {/* Table Section */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Data Table</h3>
        </div>
        <TableVisualization data={data} summary="" />
      </div>
    </div>
  );
}