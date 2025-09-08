"use client";

import { motion } from "framer-motion";
import MapCard from "./MapCard";
import DataTableCard from "./DataTableCard";
import Chart from "./Chart";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  kind?: "map" | "table" | "chart";
  map?: { lat: number; lng: number; zoom?: number; points?: { lat: number; lng: number; summary: any }[] };
  table?: { columns: string[]; rows: (string | number)[][] };
  chart?: { type: 'line' | 'bar' | 'scatter' | 'pie' | 'doughnut' | 'polarArea' | 'radar' | 'bubble'; data: any[] };
  timestamp?: string;
  full_response?: any;
};

const transformChartData = (chart: { type: string; data: any }) => {
  // If data is already in the correct format for Chart.js, return it.
  if (chart.data && chart.data.labels && chart.data.datasets) {
    return chart.data;
  }

  // If data is not an array or is empty, return an empty chart structure to prevent crashes.
  if (!Array.isArray(chart.data) || chart.data.length === 0) {
    return { labels: [], datasets: [] };
  }

  const firstItem = chart.data[0];
  const keys = Object.keys(firstItem);

  let labels;
  let datasets;

  // Handle the original time/value format
  if ('time' in firstItem && 'value' in firstItem) {
    labels = chart.data.map((d: any) => new Date(d.time * 1000).toLocaleDateString());
    const values = chart.data.map((d: any) => d.value);
    datasets = [
      {
        label: chart.type.charAt(0).toUpperCase() + chart.type.slice(1),
        data: values,
        backgroundColor: "rgba(59, 130, 246, 0.5)",
        borderColor: "rgba(59, 130, 246, 1)",
        borderWidth: 1,
      },
    ];
    
    if (chart.type === 'scatter' || chart.type === 'bubble') {
        datasets[0].data = chart.data.map((d: any) => ({ x: d.time, y: d.value, r: d.value / 10 }));
    }

  } else if (keys.length >= 2) {
    // Handle a generic format with at least two keys.
    // Assume the first key is for the labels (x-axis) and the second is for the data (y-axis).
    const labelKey = keys[0];
    const dataKey = keys[1];
    labels = chart.data.map((d: any) => d[labelKey]);
    const values = chart.data.map((d: any) => d[dataKey]);
    datasets = [
      {
        label: dataKey.charAt(0).toUpperCase() + dataKey.slice(1),
        data: values,
        backgroundColor: "rgba(59, 130, 246, 0.5)",
        borderColor: "rgba(59, 130, 246, 1)",
        borderWidth: 1,
      },
    ];

    if (chart.type === 'scatter' || chart.type === 'bubble') {
        datasets[0].data = chart.data.map((d: any) => ({ x: d[labelKey], y: d[dataKey], r: d[dataKey] / 10 }));
    }

  } else {
    // Fallback for unknown formats.
    return { labels: [], datasets: [] };
  }

  return { labels, datasets };
};

export default function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="space-y-6">
      {messages.map((m) => (
        <motion.div
          key={m.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.16 }}
          className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
        >
          <div
            className={[
              m.kind === "chart" ? "max-w-[95%] w-full" : "max-w-[85%]",
              "leading-relaxed",
              m.role === "user"
                ? "liquid-glass liquid-radius px-4 py-3"
                : "liquid-glass liquid-radius px-4 py-3",
                m.kind === "map" ? "w-full" : ""
            ].join(" ")}
          >
            {m.role === "user" && (
              <div className="text-[15px] whitespace-pre-wrap">{m.content}</div>
            )}
            {m.role === "assistant" && !m.kind && (
              <div className="text-[15px] whitespace-pre-wrap">{m.content}</div>
            )}

            {m.kind === "map" && m.map && (
              <div className="mt-3">
                {/* maps in a glass card - disable backdrop-filter for map container */}
                <div className="liquid-glass liquid-radius p-1" style={{ backdropFilter: 'none', WebkitBackdropFilter: 'none' }}>
                  <MapCard lat={m.map.lat} lng={m.map.lng} zoom={m.map.zoom ?? 12} points={m.map.points} />
                </div>
              </div>
            )}

            {m.kind === "table" && m.table && (
              <div className="mt-3">
                <div className="liquid-glass liquid-radius p-3 overflow-x-auto">
                  <DataTableCard columns={m.table.columns} rows={m.table.rows} />
                </div>
              </div>
            )}

            {m.kind === "chart" && m.chart && (
              <div className="mt-3">
                <div className="liquid-glass liquid-radius p-3 w-full">
                  <Chart
                    chartType={m.chart.type}
                    data={transformChartData(m.chart)}
                    title={`${m.chart.type.charAt(0).toUpperCase() + m.chart.type.slice(1)} Chart`}
                    width="100%"
                    height="400px"
                  />
                </div>
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}