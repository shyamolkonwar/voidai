'use client';

import { ApiResponse } from '@/types/api';
import { MapVisualization } from './MapVisualization';
import { TableVisualization } from './TableVisualization';
import { TextVisualization } from './TextVisualization';
import { BarChart3 } from 'lucide-react';

interface VisualizationPanelProps {
  response: ApiResponse | null;
}

export function VisualizationPanel({ response }: VisualizationPanelProps) {
  if (!response) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <BarChart3 className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready for Ocean Data
          </h3>
          <p className="text-gray-600 text-sm max-w-sm">
            Start a conversation to see ocean data visualizations appear here. 
            Ask about temperature patterns, marine life distributions, or water quality metrics.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 bg-gray-50">
      {response.type === 'map' && (
        <MapVisualization data={response.data} summary={response.summary} />
      )}
      
      {response.type === 'table' && (
        <TableVisualization data={response.data} summary={response.summary} />
      )}
      
      {response.type === 'text' && (
        <TextVisualization summary={response.summary} />
      )}
    </div>
  );
}