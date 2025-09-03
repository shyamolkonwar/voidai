'use client';

interface TextVisualizationProps {
  summary: string;
}

export function TextVisualization({ summary }: TextVisualizationProps) {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-gray-800 leading-relaxed">
          {summary}
        </div>
      </div>
    </div>
  );
}