"use client";
import React from "react";
import { Pie, Bar } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from "chart.js";
import { AnalyticsBreakdownItem } from "@/lib/types";

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

interface PieChartContainerProps {
  data: AnalyticsBreakdownItem[];
  dataKey: keyof AnalyticsBreakdownItem;
  nameKey: keyof AnalyticsBreakdownItem;
  title: string;
  description: string;
  className?: string;
}

export function PieChartContainer({ data, dataKey, nameKey, title, description, className }: PieChartContainerProps) {
  // Defensive check: Jika data kosong/undefined, return null atau pesan kosong
  if (!data || data.length === 0) {
    return (
      <div className={`${className} flex items-center justify-center border-2 border-dashed rounded-lg`}>
        <p className="text-gray-400 text-sm">No data available for {title}</p>
      </div>
    );
  }

  // Calculate total for percentage calculation
  const total = data.reduce((sum, item) => sum + (Number(item[dataKey]) || 0), 0);

  const chartData = {
    labels: data.map((item) => String(item[nameKey])),
    datasets: [
      {
        data: data.map((item) => Number(item[dataKey]) || 0),
        backgroundColor: [
          "#3B82F6", // blue-500
          "#10B981", // emerald-500
          "#F59E0B", // amber-500
          "#EF4444", // red-500
          "#8B5CF6", // violet-500
          "#06B6D4", // cyan-500
          "#84CC16", // lime-500
          "#F97316", // orange-500
          "#6366F1", // indigo-500
          "#EC4899", // pink-500
        ],
        borderWidth: 2,
        borderColor: "#ffffff",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom" as const,
        labels: {
          padding: 20,
          usePointStyle: true,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const label = context.label || "";
            const value = context.parsed;
            // Cegah pembagian dengan nol (NaN)
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
            return `${label}: ${value.toLocaleString()} (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div className={className}>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <div className="text-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
            <p className="text-sm text-gray-600">{description}</p>
          </div>

          <div className="relative" style={{ height: "300px" }}>
            <Pie data={chartData} options={options} />
          </div>
        </div>

        {/* Value + Percentage breakdown table */}
        <div className="mt-4 overflow-y-auto max-h-[300px]">
          <div className="text-sm font-medium text-gray-700 mb-2">Breakdown by Value & Percentage:</div>
          <div className="space-y-1">
            {data.map((item, index) => {
              const value = Number(item[dataKey]) || 0;
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
              return (
                <div key={index} className="flex justify-between items-center text-sm p-1 hover:bg-gray-50 rounded">
                  <span className="text-gray-600 truncate mr-2">{String(item[nameKey])}</span>
                  <span className="font-medium whitespace-nowrap">
                    {Math.round(value).toLocaleString()} ({percentage}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

interface BarChartContainerProps {
  data: AnalyticsBreakdownItem[];
  dataKey: keyof AnalyticsBreakdownItem;
  nameKey: keyof AnalyticsBreakdownItem;
  title: string;
  description: string;
  className?: string;
}

export function BarChartContainer({ data, dataKey, nameKey, title, description, className }: BarChartContainerProps) {
  const chartData = {
    labels: data.map((item) => item[nameKey] as string),
    datasets: [
      {
        label: title,
        data: data.map((item) => item[dataKey] as number),
        backgroundColor: "#3B82F6",
        borderColor: "#2563EB",
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: title,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className={className}>
      <div className="text-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>

      <div className="relative" style={{ height: "300px" }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
