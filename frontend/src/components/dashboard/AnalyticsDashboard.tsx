"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { AnalyticsPanel } from "./AnalyticsPanel";
import { DimensionOptions, PanelState } from "@/lib/types";

interface AnalyticsDashboardProps {
  compareOn: boolean;
  setCompareOn: React.Dispatch<React.SetStateAction<boolean>>;
  panelA: PanelState;
  setPanelA: React.Dispatch<React.SetStateAction<PanelState>>;
  panelB: PanelState;
  setPanelB: React.Dispatch<React.SetStateAction<PanelState>>;
  dimensions: DimensionOptions;
  fetchAnalytics: (panel: "A" | "B") => void;
  formatCurrency: (n: number) => string;
  formatDateRange: (from: Date | undefined, to: Date | undefined) => string;
  computeOccupancyPct: (data: PanelState["data"], totalRooms: number) => number;
}

export function AnalyticsDashboard({
  compareOn,
  setCompareOn,
  panelA,
  setPanelA,
  panelB,
  setPanelB,
  dimensions,
  fetchAnalytics,
  formatCurrency,
  formatDateRange,
  computeOccupancyPct,
}: AnalyticsDashboardProps) {
  return (
    <Card className="shadow-md">
      <CardHeader className="space-y-4">
        {/* Judul Kartu */}
        <CardTitle className="flex items-center gap-2 font-semibold">
          <BarChart3 className="w-6 h-6" />
          Analytics Dashboard
        </CardTitle>
        {/* Switch untuk Mode Perbandingan */}
        <div className="flex items-center gap-2">
          <Switch id="compareToggle" checked={compareOn} onCheckedChange={setCompareOn} />
          <label htmlFor="compareToggle" className="text-normal font-medium text-gray-700">
            Enable Compare Mode
          </label>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        {/* Tampilan kondisional berdasarkan state 'compareOn' */}
        {compareOn ? (
          <ResizablePanelGroup direction="horizontal" className="min-h-[600px] rounded-lg border">
            <ResizablePanel defaultSize={50} minSize={30}>
              <div className="p-6 h-full overflow-y-auto">
                <AnalyticsPanel
                  panelId="A"
                  state={panelA}
                  setState={setPanelA}
                  dimensions={dimensions}
                  onApply={fetchAnalytics}
                  formatCurrency={formatCurrency}
                  formatDateRange={formatDateRange}
                  computeOccupancyPct={computeOccupancyPct}
                />
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={50} minSize={30}>
              <div className="p-6 h-full overflow-y-auto">
                <AnalyticsPanel
                  panelId="B"
                  state={panelB}
                  setState={setPanelB}
                  dimensions={dimensions}
                  onApply={fetchAnalytics}
                  isDisabled={!compareOn}
                  formatCurrency={formatCurrency}
                  formatDateRange={formatDateRange}
                  computeOccupancyPct={computeOccupancyPct}
                />
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          // Tampilan Satu Panel (Mode Standar)
          <div className="px-4">
            <AnalyticsPanel
              panelId="A"
              state={panelA}
              setState={setPanelA}
              dimensions={dimensions}
              onApply={fetchAnalytics}
              formatCurrency={formatCurrency}
              formatDateRange={formatDateRange}
              computeOccupancyPct={computeOccupancyPct}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
