"use client";
import { useState, useEffect } from "react";
import axios from "axios";
import { DashboardStats, DimensionOptions, PanelState, AnalyticsResponse } from "../../lib/types";

import { Header } from "../../components/dashboard/Header";
import { StatCards } from "../../components/dashboard/StatCards";
import { AnalyticsDashboard } from "../../components/dashboard/AnalyticsDashboard";
import { UploadModal } from "../../components/dashboard/UploadModal";

// HELPER DATE
const formatDateLocal = (date: Date | undefined | null) => {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const [compareOn, setCompareOn] = useState(false);
  const [dimensions, setDimensions] = useState<DimensionOptions>({
    segment: [],
    local_region: [],
    nationality: [],
    room_type_desc: [],
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
      const statsRes = await axios.get(`${API_BASE}/dashboard/stats`, { withCredentials: true });

      const responseData = statsRes.data;

      if (responseData && Array.isArray(responseData.data) && responseData.data.length > 0) {
        const actualStats = responseData.data[0];

        // console.log("✅ Stats Loaded:", actualStats);
        setStats(actualStats);

        if (actualStats.latest_depart_date) {
          const endDate = new Date(actualStats.latest_depart_date);
          const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
          const newDateRange = { from: startDate, to: endDate };

          setPanelA((prev) => ({ ...prev, dateRange: newDateRange }));
          setPanelB((prev) => ({ ...prev, dateRange: newDateRange }));
        }
      } else {
        console.warn("⚠️ Format data tidak sesuai atau kosong:", responseData);
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
          start: formatDateLocal(dateRange.from),
          end: formatDateLocal(dateRange.to),
        },
        withCredentials: true,
      });

      const responseBody = res.data;

      if (responseBody && Array.isArray(responseBody.data) && responseBody.data.length > 0) {
        const dimensionsData = responseBody.data[0];

        setDimensions(dimensionsData);
      } else {
        console.warn("⚠️ Format dimensi tidak sesuai (bukan array), mencoba raw:", responseBody);
        setDimensions(responseBody);
      }
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

    const params = {
      start: formatDateLocal(ps.dateRange.from),
      end: formatDateLocal(ps.dateRange.to),
      group_by: ps.group_by,
      segment_in: ps.segmentSelected || undefined,
      room_type_in: ps.roomTypeSelected || undefined,
      local_region_in: ps.localRegionSelected || undefined,
      nationality_in: ps.nationalitySelected || undefined,
      top_n: ps.topN,
      include_other: ps.includeOther,
    };

    try {
      console.log(`📤 Fetching Analytics Panel ${panel}...`, params);

      const res = await axios.get<AnalyticsResponse>(`${API_BASE}/analytics/aggregate`, {
        params,
        withCredentials: true,
      });

      const responseBody: any = res.data;
      let analyticsData = responseBody;

      if (responseBody && Array.isArray(responseBody.data) && responseBody.data.length > 0) {
        analyticsData = responseBody.data[0];
        console.log(`✅ (Unwrapped) Analytics Data Panel ${panel}:`, analyticsData);
      } else {
        console.log(`✅ (Raw) Analytics Data Panel ${panel}:`, analyticsData);
      }

      setPs((prev) => ({ ...prev, data: res.data, loading: false }));
    } catch (e: any) {
      console.error(`❌ Error Fetching Analytics Panel ${panel}:`, e);

      let errorMessage = "Failed to fetch analytics";

      if (e.response && e.response.data) {
        const data = e.response.data;

        if (data.messages) {
          errorMessage = data.messages;
        } else if (data.detail) {
          errorMessage = typeof data.detail === "object" ? JSON.stringify(data.detail) : data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (e.response.status === 500) {
          errorMessage = "Internal Server Error (500). Cek konfigurasi Database Backend.";
        }
      } else if (e.message) {
        errorMessage = e.message;
      }

      setPs((prev) => ({ ...prev, error: errorMessage, loading: false }));
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

    const totals: any = data.totals || {};
    const nights = totals.room_sold || totals.occupied_room_nights || 0;

    const days = data.period?.days || 1;
    const denom = totalRooms * days;
    return denom > 0 ? Math.min(100, (nights / denom) * 100) : 0;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header page="dashboard" onUploadClick={() => setIsUploadModalOpen(true)} />
      <main className="mx-auto max-w-7xl p-4 sm:px-6 lg:px-8 sm:py-6">
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
