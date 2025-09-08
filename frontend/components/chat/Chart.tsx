"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar, Pie, Doughnut, PolarArea, Radar, Scatter, Bubble } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Chart({
  chartType,
  data,
  title,
  width = "100%",
  height = "400px"
}: {
  chartType: string;
  data: any;
  title?: string;
  width?: string | number;
  height?: string | number;
}) {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: title,
      },
    },
  };

  const renderChart = () => {
    switch (chartType.toLowerCase()) {
      case "line":
        return <Line options={options} data={data} />;
      case "bar":
        return <Bar options={options} data={data} />;
      case "pie":
        return <Pie options={options} data={data} />;
      case "doughnut":
        return <Doughnut options={options} data={data} />;
      case "polararea":
        return <PolarArea options={options} data={data} />;
      case "radar":
        return <Radar options={options} data={data} />;
      case "scatter":
        return <Scatter options={options} data={data} />;
      case "bubble":
        return <Bubble options={options} data={data} />;
      default:
        return <Line options={options} data={data} />;
    }
  };

  return (
    <div style={{ width, height }}>
      {renderChart()}
    </div>
  );
}
