"use client";

import { Button } from "@/components/ui/button";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { MultiSelect } from "@/components/ui/multi-select";
import { PieChartContainer } from "@/components/ui/chart";

import { DimensionOptions, GroupBy, PanelState } from "@/lib/types";

interface AnalyticsPanelProps {
  panelId: "A" | "B";
  state: PanelState;
  setState: React.Dispatch<React.SetStateAction<PanelState>>;
  dimensions: DimensionOptions;
  onApply: (panel: "A" | "B") => void;
  formatCurrency: (n: number) => string;
  formatDateRange: (from: Date | undefined, to: Date | undefined) => string;
  computeOccupancyPct: (data: PanelState["data"], totalRooms: number) => number;
  isDisabled?: boolean;
}

export function AnalyticsPanel({
  panelId,
  state,
  setState,
  dimensions,
  onApply,
  formatCurrency,
  formatDateRange,
  computeOccupancyPct,
  isDisabled = false,
}: AnalyticsPanelProps) {
  // Handler untuk memperbarui state berdasarkan perubahan pada field tertentu
  const handleStateChange = <K extends keyof PanelState>(field: K, value: PanelState[K]) => {
    setState((prevState) => ({ ...prevState, [field]: value }));
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold mb-2">Panel {panelId}</h3>

      {/* Date Range Picker */}
      <div className="mb-4 space-y-2">
        <label className="text-sm text-gray-600 mb-2 block">Date Range</label>
        <DateRangePicker
          dateRange={state.dateRange}
          onDateRangeChange={(range) => handleStateChange("dateRange", range)}
          placeholder={`Select date range for Panel ${panelId}`}
          className="hover:border-primary"
        />
      </div>

      {/* Filters dan Options */}
      <Accordion type="single" collapsible className="w-full mb-4">
        <AccordionItem value={`filters-${panelId}`}>
          <AccordionTrigger className="text-sm font-medium">Advanced Filters & Dimensions</AccordionTrigger>
          <AccordionContent className="space-y-4 pt-4">
            {/* Group By Dropdown */}
            <div className="space-y-2">
              <label className="text-sm text-gray-600 font-medium">Group By</label>
              <select
                value={state.group_by}
                onChange={(e) => handleStateChange("group_by", e.target.value as GroupBy)}
                className="w-full border rounded px-2 py-1 mt-1 hover:border-primary bg-white"
              >
                <option value="none">None</option>
                <option value="segment">Segment</option>
                <option value="room_type">Room Type</option>
                <option value="local_region">City (local_region)</option>
                <option value="nationality">Nationality</option>
                <option value="age_group">Age Group</option>
              </select>
            </div>

            {/* Filter Segments */}
            <div className="space-y-2">
              <label className="text-sm text-gray-600 font-medium">Select segments</label>
              <MultiSelect
                options={dimensions.segment}
                selected={state.segmentSelected.split(",").filter(Boolean)}
                onChange={(selected) => handleStateChange("segmentSelected", selected.join(","))}
                placeholder="Select segments..."
                searchPlaceholder="Search segments..."
                className="mt-1 hover:border-primary"
              />
            </div>

            {/* Filter Room Types */}
            <div className="space-y-2">
              <label className="text-sm text-gray-600 font-medium">Select room types</label>
              <MultiSelect
                options={dimensions.room_type}
                selected={state.roomTypeSelected.split(",").filter(Boolean)}
                onChange={(selected) => handleStateChange("roomTypeSelected", selected.join(","))}
                placeholder="Select room types..."
                searchPlaceholder="Search room types..."
                className="mt-1 hover:border-primary"
              />
            </div>

            {/* Filter Cities */}
            <div className="space-y-2">
              <label className="text-sm text-gray-600 font-medium">Select cities</label>
              <MultiSelect
                options={dimensions.local_region}
                selected={state.localRegionSelected.split(",").filter(Boolean)}
                onChange={(selected) => handleStateChange("localRegionSelected", selected.join(","))}
                placeholder="Select cities..."
                searchPlaceholder="Search cities..."
                className="mt-1 hover:border-primary"
              />
            </div>

            {/* Filter Nationalities */}
            <div className="space-y-2">
              <label className="text-sm text-gray-600 font-medium">Select nationalities</label>
              <MultiSelect
                options={dimensions.nationality}
                selected={state.nationalitySelected.split(",").filter(Boolean)}
                onChange={(selected) => handleStateChange("nationalitySelected", selected.join(","))}
                placeholder="Select nationalities..."
                searchPlaceholder="Search nationalities..."
                className="mt-1 hover:border-primary"
              />
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value={`options-${panelId}`}>
          <AccordionTrigger className="text-sm font-medium">Display Options & Settings</AccordionTrigger>
          <AccordionContent className="space-y-4 pt-4">
            <div className="grid grid-cols-2 gap-4">
              {/* Top N Input */}
              <div className="space-y-2">
                <label className="text-sm text-gray-600 font-medium">Top N</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={state.topN || 6}
                  onChange={(e) => handleStateChange("topN", Number(e.target.value))}
                  className="w-full border rounded px-2 py-1 mt-1 hover:border-primary"
                />
              </div>

              {/* Total Rooms Input */}
              <div className="space-y-2">
                <label className="text-sm text-gray-600 font-medium">Total Rooms</label>
                <input
                  type="number"
                  min={1}
                  value={state.totalRooms}
                  onChange={(e) => handleStateChange("totalRooms", Number(e.target.value))}
                  className="w-full border rounded px-2 py-1 mt-1 hover:border-primary"
                />
              </div>
            </div>

            {/* Include Other Checkbox */}
            <div className="flex items-center gap-2">
              <input
                id={`includeOther${panelId}`}
                type="checkbox"
                checked={state.includeOther}
                onChange={(e) => handleStateChange("includeOther", e.target.checked)}
              />
              <label htmlFor={`includeOther${panelId}`} className="text-sm text-gray-600">
                Include Other
              </label>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Tombol Apply dan pesan error */}
      <div className="flex gap-2 mb-4 items-center">
        <Button onClick={() => onApply(panelId)} disabled={isDisabled || state.loading}>
          {state.loading ? "Loading…" : `Apply`}
        </Button>
        {state.error && <span className="text-red-600 text-sm">{state.error}</span>}
      </div>

      {/* Hasil Analitik */}
      <div className="border-t pt-4">
        <h4 className="font-semibold mb-4">Results</h4>
        {state.data ? (
          <div className="space-y-8">
            {/* Revenue Section */}
            <div className="mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg mb-4">
                <div className="text-2xl font-bold text-blue-600">{formatCurrency(state.data.totals.revenue_sum)}</div>
                <div className="text-sm text-gray-600">Total Revenue</div>
                <div className="text-xs text-gray-500 mt-1">{formatDateRange(state.dateRange?.from, state.dateRange?.to)}</div>
              </div>
              <PieChartContainer
                data={state.data.breakdown}
                dataKey="revenue_sum"
                nameKey="key"
                title="Revenue Breakdown"
                description={`By ${state.group_by}`}
                className="min-h-[300px]"
              />
            </div>

            {/* Occupancy Section */}
            <div className="mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg mb-4">
                <div className="text-2xl font-bold text-green-600">{computeOccupancyPct(state.data, state.totalRooms).toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Occupancy Rate</div>
                <div className="text-xs text-gray-500 mt-1">{formatDateRange(state.dateRange?.from, state.dateRange?.to)}</div>
              </div>
              <PieChartContainer
                data={state.data.breakdown}
                dataKey="occupied_room_nights"
                nameKey="key"
                title="Occupancy Breakdown"
                description={`By ${state.group_by}`}
                className="min-h-[300px]"
              />
            </div>

            {/* ARR Section */}
            <div className="mb-6">
              <div className="text-center p-4 bg-purple-50 rounded-lg mb-4">
                <div className="text-2xl font-bold text-purple-600">{formatCurrency(state.data.totals.arr_simple)}</div>
                <div className="text-sm text-gray-600">Average Room Rate</div>
                <div className="text-xs text-gray-500 mt-1">{formatDateRange(state.dateRange?.from, state.dateRange?.to)}</div>
              </div>
              <PieChartContainer
                data={state.data.breakdown}
                dataKey="arr_simple"
                nameKey="key"
                title="ARR Breakdown"
                description={`By ${state.group_by}`}
                className="min-h-[300px]"
              />
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500 text-center py-10">No data. Click Apply to load analytics.</div>
        )}
      </div>
    </div>
  );
}
