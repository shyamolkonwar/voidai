"use client";

import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, LineStyle, LineSeries, HistogramSeries } from "lightweight-charts";

/**
 * Interactive chart visualization using lightweight-charts
 * Supports line, bar, and scatter charts with proper visualization
 */
export default function ChartCard({
  chartType,
  data,
  title,
  width = "100%",
  height = "300px"
}: {
  chartType: string;
  data: any[];
  title?: string;
  width?: string | number;
  height?: string | number;
}) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart: IChartApi = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { color: "transparent" },
        textColor: "rgba(255, 255, 255, 0.7)",
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.1)" },
        horzLines: { color: "rgba(255, 255, 255, 0.1)" },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    if (!chart) {
      console.error("Chart initialization failed or chart object is invalid.");
      return; // Exit early if chart is not valid
    }

    chartRef.current = chart;

    // Prepare data for lightweight-charts
    const chartData = data.map(item => ({
      time: item.time || item.timestamp || Date.now() / 1000,
      value: item.value,
    }));

    let series;
    
    switch (chartType) {
      case "line":
        series = chart.addSeries(LineSeries);
        series.applyOptions({
          color: "#3b82f6",
          lineWidth: 2,
        });
        break;
      case "bar":
        series = chart.addSeries(HistogramSeries);
        series.applyOptions({
          color: "#10b981",
        });
        break;
      case "scatter":
        series = chart.addSeries(LineSeries);
        series.applyOptions({
          color: "#ef4444",
          lineWidth: 1,
          crosshairMarkerVisible: true,
          crosshairMarkerRadius: 4,
        });
        break;
      default:
        series = chart.addSeries(LineSeries);
        series.applyOptions({
          color: "#3b82f6",
          lineWidth: 2,
        });
    }

    series.setData(chartData);

    // Handle window resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [chartType, data]);

  return (
    <div className="w-full">
      {title && (
        <div className="text-sm font-medium text-white/80 mb-2">{title}</div>
      )}
      <div
        style={{ width, height }}
        className="rounded-lg overflow-hidden bg-gradient-to-br from-slate-800 to-slate-900 relative"
      >
        <div
          ref={chartContainerRef}
          className="w-full h-full"
          style={{ width, height }}
        />
        {data.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-white/50 text-sm">
            No data available
          </div>
        )}
      </div>
    </div>
  );
}