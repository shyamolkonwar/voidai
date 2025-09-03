'use client';

import { TableData } from '@/types/api';

interface TableVisualizationProps {
  data: TableData[];
  summary: string;
}

export function TableVisualization({ data, summary }: TableVisualizationProps) {
  if (!data.length) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8 text-gray-500">
          No data available
        </div>
        <div className="text-sm text-gray-700 leading-relaxed">
          {summary}
        </div>
      </div>
    );
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {columns.map((column) => (
                  <th
                    key={column}
                    className="px-4 py-3 text-left font-medium text-gray-900 uppercase tracking-wider"
                  >
                    {column.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr
                  key={index}
                  className={`${
                    index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                  } hover:bg-gray-100 transition-colors`}
                >
                  {columns.map((column) => (
                    <td key={column} className="px-4 py-3 text-gray-800">
                      {formatCellValue(row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="text-sm text-gray-700 leading-relaxed">
        {summary}
      </div>
    </div>
  );
}

function formatCellValue(value: any): string {
  if (value === null || value === undefined) {
    return '-';
  }
  
  if (typeof value === 'number') {
    return value.toLocaleString();
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  
  return String(value);
}