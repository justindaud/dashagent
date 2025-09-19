"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { AnalyticsPanel } from "./AnalyticsPanel";
import { DimensionOptions, PanelState } from "@/lib/types";
import { Separator } from "@/components/ui/separator";

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
    <Card className="shadow-sm">
      <CardHeader className="space-y-4 px-4 sm:px-6">
        <CardTitle className="flex items-center gap-2 font-semibold">
          <BarChart3 className="w-6 h-6" />
          Analytics Dashboard
        </CardTitle>
        <div className="flex items-center gap-2">
          <Switch id="compareToggle" checked={compareOn} onCheckedChange={setCompareOn} />
          <label htmlFor="compareToggle" className="text-sm sm:text-base font-medium text-gray-700">
            Enable Compare Mode
          </label>
        </div>
      </CardHeader>
      <CardContent className="pt-4 sm:pt-6">
        {compareOn ? (
          <>
            <div className="hidden lg:block">
              <ResizablePanelGroup direction="horizontal" className="min-h-[600px] rounded-lg border">
                <ResizablePanel defaultSize={50} minSize={30}>
                  <div className="p-4 sm:p-6 h-full overflow-y-auto">
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
                  <div className="p-4 sm:p-6 h-full overflow-y-auto">
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
            </div>

            <div className="lg:hidden flex flex-col gap-6 px-2 sm:px-4">
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
              <Separator />
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
          </>
        ) : (
          <div className="px-2 sm:px-4">
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
