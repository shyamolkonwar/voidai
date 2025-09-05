"use client";

import { motion } from "framer-motion";
import MapCard from "./MapCard";
import DataTableCard from "./DataTableCard";
import ChartCard from "./ChartCard";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  kind?: "map" | "table" | "chart";
  map?: { lat: number; lng: number; zoom?: number; points?: { lat: number; lng: number; summary: any }[] };
  table?: { columns: string[]; rows: (string | number)[][] };
  chart?: { type: 'line' | 'bar' | 'scatter'; data: any[] };
  timestamp?: string;
  full_response?: any;
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
                  <ChartCard
                    chartType={m.chart.type.charAt(0).toUpperCase() + m.chart.type.slice(1) as any}
                    data={m.chart.data}
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
