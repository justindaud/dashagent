"use client";
// import AuthGuard from "@/components/auth/AuthGuard";
import { useState, useEffect } from "react";
import axios from "axios";
import { DashboardStats, DimensionOptions, PanelState, AnalyticsResponse } from "../lib/types";

import { Header } from "../components/dashboard/Header";
import { StatCards } from "../components/dashboard/StatCards";
import { AnalyticsDashboard } from "../components/dashboard/AnalyticsDashboard";
import { UploadModal } from "../components/dashboard/UploadModal";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const [compareOn, setCompareOn] = useState(false);
  const [dimensions, setDimensions] = useState<DimensionOptions>({
    segment: [],
    room_type: [],
    local_region: [],
    nationality: [],
  });

  const today = new Date();
  const defaultEnd = new Date(today);
  const defaultStart = new Date(today.getTime() - 29 * 24 * 60 * 60 * 1000);

  const initialPanelState: Omit<PanelState, "dateRange"> = {
    group_by: "segment",
    segmentSelected: "",
    roomTypeSelected: "",
    localRegionSelected: "",
    nationalitySelected: "",
    topN: 6,
    includeOther: true,
    totalRooms: 94,
    data: null,
    loading: false,
    error: null,
  };

  const [panelA, setPanelA] = useState<PanelState>({
    ...initialPanelState,
    dateRange: { from: defaultStart, to: defaultEnd },
  });
  const [panelB, setPanelB] = useState<PanelState>({
    ...initialPanelState,
    dateRange: { from: defaultStart, to: defaultEnd },
  });

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  const fetchDashboardData = async () => {
    try {
      const statsRes = await axios.get(`${API_BASE}/dashboard/stats`);
      setStats(statsRes.data);

      if (statsRes.data.latest_depart_date) {
        const endDate = new Date(statsRes.data.latest_depart_date);
        const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
        const newDateRange = { from: startDate, to: endDate };
        setPanelA((prev) => ({ ...prev, dateRange: newDateRange }));
        setPanelB((prev) => ({ ...prev, dateRange: newDateRange }));
      }
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
    }
  };

  const fetchDimensions = async () => {
    const dateRange = panelA.dateRange;
    if (!dateRange?.from || !dateRange?.to) return;
    try {
      const res = await axios.get(`${API_BASE}/analytics/dimensions`, {
        params: {
          start: dateRange.from.toISOString().slice(0, 10),
          end: dateRange.to.toISOString().slice(0, 10),
        },
      });
      setDimensions(res.data);
    } catch (e) {
      console.error("Failed to fetch dimensions", e);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    fetchDimensions();
  }, [panelA.dateRange]);

  const fetchAnalytics = async (panel: "A" | "B") => {
    const ps = panel === "A" ? panelA : panelB;
    const setPs = panel === "A" ? setPanelA : setPanelB;
    if (!ps.dateRange?.from || !ps.dateRange?.to) return;

    setPs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const params = {
        start: ps.dateRange.from.toISOString().slice(0, 10),
        end: ps.dateRange.to.toISOString().slice(0, 10),
        group_by: ps.group_by,
        segment_in: ps.segmentSelected || undefined,
        room_type_in: ps.roomTypeSelected || undefined,
        local_region_in: ps.localRegionSelected || undefined,
        nationality_in: ps.nationalitySelected || undefined,
        top_n: ps.topN,
        include_other: ps.includeOther,
      };
      const res = await axios.get<AnalyticsResponse>(`${API_BASE}/analytics/aggregate`, { params });
      setPs((prev) => ({ ...prev, data: res.data, loading: false }));
    } catch (e: any) {
      setPs((prev) => ({ ...prev, error: e?.response?.data?.detail || "Failed to fetch analytics", loading: false }));
    }
  };

  const formatCurrency = (n: number | undefined | null) => {
    return (n || 0).toLocaleString("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });
  };

  const formatDateRange = (from: Date | undefined, to: Date | undefined) => {
    if (!from || !to) return "";
    const options: Intl.DateTimeFormatOptions = { year: "numeric", month: "short", day: "numeric" };
    return `${from.toLocaleDateString("id-ID", options)} - ${to.toLocaleDateString("id-ID", options)}`;
  };

  const computeOccupancyPct = (data: AnalyticsResponse | null, totalRooms: number) => {
    if (!data || !totalRooms) return 0;
    const nights = data.totals.occupied_room_nights || 0;
    const days = data.period.days || 1;
    const denom = totalRooms * days;
    return denom > 0 ? Math.min(100, (nights / denom) * 100) : 0;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header page="dashboard" onUploadClick={() => setIsUploadModalOpen(true)} />
      <main className="max-w-7xl mx-auto sm:px-6 lg:px-8 py-4">
        <StatCards stats={stats} />

        <AnalyticsDashboard
          compareOn={compareOn}
          setCompareOn={setCompareOn}
          panelA={panelA}
          setPanelA={setPanelA}
          panelB={panelB}
          setPanelB={setPanelB}
          dimensions={dimensions}
          fetchAnalytics={fetchAnalytics}
          formatCurrency={formatCurrency}
          formatDateRange={formatDateRange}
          computeOccupancyPct={computeOccupancyPct}
        />
      </main>

      <UploadModal
        isOpen={isUploadModalOpen}
        onOpenChange={setIsUploadModalOpen}
        onUploadSuccess={() => {
          fetchDashboardData();
          fetchDimensions();
        }}
      />
    </div>
  );
}
