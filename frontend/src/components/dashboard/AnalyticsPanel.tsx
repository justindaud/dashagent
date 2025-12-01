"use client";

import { Button } from "@/components/ui/button";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { MultiSelect } from "@/components/ui/multi-select";
import { PieChartContainer } from "@/components/ui/chart";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

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

const ResultsSkeleton = () => (
  <div className="space-y-8 animate-pulse">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="rounded-lg border-2">
        <div className="p-4 bg-gray-100 rounded-t-lg mb-4 space-y-2">
          <Skeleton className="h-6 w-1/3 mx-auto" />
          <Skeleton className="h-8 w-1/2 mx-auto" />
          <Skeleton className="h-4 w-2/3 mx-auto" />
        </div>
        <div className="p-4">
          <Skeleton className="h-[300px] w-full" />
        </div>
      </div>
    ))}
  </div>
);

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
  const handleStateChange = <K extends keyof PanelState>(field: K, value: PanelState[K]) => {
    setState((prevState) => ({ ...prevState, [field]: value }));
  };

  // --- SAFE DATA UNWRAPPING ---
  // Memastikan data aman dibaca, baik terbungkus array maupun object langsung
  const rawData: any = state.data;

  const actualData = rawData && Array.isArray(rawData.data) && rawData.data.length > 0 ? rawData.data[0] : rawData;

  // Helper untuk akses totals dengan aman
  const totals: any = actualData?.totals || {};

  // Mapping key dari backend (revenue_sum, arr_simple)
  const totalRevenue = totals.revenue_sum || 0;
  const totalArr = totals.arr_simple || 0;

  // Pastikan breakdown selalu array
  const breakdownData = Array.isArray(actualData?.breakdown) ? actualData.breakdown : [];

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

      <Accordion type="single" collapsible className="w-full mb-4">
        <AccordionItem value={`filters-${panelId}`}>
          <AccordionTrigger className="text-sm font-medium">Advanced Filters & Dimensions</AccordionTrigger>
          <AccordionContent className="pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-gray-600 font-medium">Group By</label>
                <Select value={state.group_by} onValueChange={(value) => handleStateChange("group_by", value as GroupBy)}>
                  <SelectTrigger className="w-full bg-white hover:border-primary">
                    <SelectValue placeholder="Select how to group data" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="segment">Segment</SelectItem>
                    <SelectItem value="room_type_desc">Room Type</SelectItem>
                    <SelectItem value="local_region">City (local_region)</SelectItem>
                    <SelectItem value="nationality">Nationality</SelectItem>
                    <SelectItem value="age_group">Age Group</SelectItem>
                  </SelectContent>
                </Select>
              </div>

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

              <div className="space-y-2">
                <label className="text-sm text-gray-600 font-medium">Select room types</label>
                <MultiSelect
                  options={dimensions.room_type_desc}
                  selected={state.roomTypeSelected.split(",").filter(Boolean)}
                  onChange={(selected) => handleStateChange("roomTypeSelected", selected.join(","))}
                  placeholder="Select room types..."
                  searchPlaceholder="Search room types..."
                  className="mt-1 hover:border-primary"
                />
              </div>

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
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value={`options-${panelId}`}>
          <AccordionTrigger className="text-sm font-medium">Display Options & Settings</AccordionTrigger>
          <AccordionContent className=" pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-gray-600 font-medium">Top N</label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={state.topN ? state.topN : ""}
                  placeholder="0"
                  onChange={(e) => {
                    handleStateChange("topN", Number(e.target.value));
                  }}
                  className="w-full hover:border-primary"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-gray-600 font-medium">Total Rooms</label>
                <Input
                  type="number"
                  min={1}
                  value={state.totalRooms ? state.totalRooms : ""}
                  placeholder="0"
                  onChange={(e) => {
                    handleStateChange("totalRooms", Number(e.target.value));
                  }}
                  className="w-full hover:border-primary"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 mt-4">
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

      <div className="flex gap-2 mb-4 items-center">
        <Button onClick={() => onApply(panelId)} disabled={isDisabled || state.loading}>
          {state.loading ? "Loading…" : `Apply`}
        </Button>
        {state.error && <span className="text-red-600 text-sm">{state.error}</span>}
      </div>

      <div className="border-t pt-4">
        <h4 className="font-semibold mb-4">Results</h4>
        {state.loading ? (
          <ResultsSkeleton />
        ) : state.data ? (
          <div className="space-y-8 ">
            {/* Revenue Section */}
            <div className="mb-4 rounded-lg border-2 border-primary">
              <div className="text-center p-4 bg-primary/10 rounded-t-lg mb-4">
                <div className="text-lg text-gray-700">Total Revenue</div>
                <div className="text-2xl font-bold text-primary">{formatCurrency(totalRevenue)}</div>
                <div className="text-xs text-gray-500 mt-1">{formatDateRange(state.dateRange?.from, state.dateRange?.to)}</div>
              </div>
              <PieChartContainer
                data={breakdownData}
                dataKey="revenue_sum"
                nameKey="key"
                title="Revenue Breakdown"
                description={`By ${state.group_by}`}
                className="min-h-[300px] p-4"
              />
            </div>

            {/* Occupancy Section */}
            <div className="mb-4 rounded-lg border-2 border-primary">
              <div className="text-center p-4 bg-primary/10 rounded-t-lg mb-4">
                <div className="text-lg text-gray-700">Occupancy Rate</div>
                <div className="text-2xl font-bold primary text-primary">
                  {/* Gunakan actualData untuk perhitungan occupancy */}
                  {computeOccupancyPct(actualData, state.totalRooms).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">{formatDateRange(state.dateRange?.from, state.dateRange?.to)}</div>
              </div>
              <PieChartContainer
                data={breakdownData}
                dataKey="room_sold"
                nameKey="key"
                title="Occupancy Breakdown"
                description={`By ${state.group_by}`}
                className="min-h-[300px] p-4"
              />
            </div>

            {/* ARR Section */}
            <div className="mb-4 rounded-lg border-2 border-primary">
              <div className="text-center p-4 bg-primary/10 rounded-t-lg mb-4">
                <div className="text-lg text-gray-700">Average Room Rate</div>
                <div className="text-2xl font-bold primary text-primary">{formatCurrency(totalArr)}</div>
                <div className="text-xs text-gray-500 mt-1">{formatDateRange(state.dateRange?.from, state.dateRange?.to)}</div>
              </div>
              <PieChartContainer
                data={breakdownData}
                dataKey="arr_simple"
                nameKey="key"
                title="ARR Breakdown"
                description={`By ${state.group_by}`}
                className="min-h-[300px] p-4"
              />
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500 text-center py-10 border rounded-lg">No data. Click Apply to load analytics.</div>
        )}
      </div>
    </div>
  );
}
