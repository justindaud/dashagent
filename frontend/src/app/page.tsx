'use client'

import { useState, useEffect } from 'react'
import { Upload, Users, Calendar, MessageCircle, CreditCard, Bot, X, Trash2, BarChart3 } from 'lucide-react'
import axios from 'axios'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { PieChartContainer } from '@/components/ui/chart'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { DateRangePicker } from '@/components/ui/date-range-picker'
import { Switch } from '@/components/ui/switch'
import { DateRange } from 'react-day-picker'
import { MultiSelect } from '@/components/ui/multi-select'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"

interface DashboardStats {
  total_guests: number
  total_reservations: number
  total_chats: number
  last_updated: string
}

interface RecentUpload {
  id: number
  filename: string
  file_type: string
  status: string
  rows_processed: number
  created_at: string
}

interface AnalyticsTotals {
  revenue_sum: number
  occupied_room_nights: number
  arr_simple: number
  bookings_count: number
}

interface AnalyticsBreakdownItem {
  key: string
  revenue_sum: number
  occupied_room_nights: number
  arr_simple: number
  bookings_count: number
}

interface AnalyticsResponse {
  period: { start: string; end: string; days: number }
  totals: AnalyticsTotals
  breakdown: AnalyticsBreakdownItem[]
}

type GroupBy = 'none' | 'segment' | 'room_type' | 'local_region' | 'nationality' | 'age_group'

interface PanelState {
  dateRange: DateRange | undefined
  group_by: GroupBy
  segmentSelected: string
  roomTypeSelected: string
  localRegionSelected: string
  nationalitySelected: string
  topN?: number
  includeOther: boolean
  totalRooms: number
  data: AnalyticsResponse | null
  loading: boolean
  error: string | null
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([])
  const [isChatbotOpen, setIsChatbotOpen] = useState(false)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedFileType, setSelectedFileType] = useState<string>('profile_tamu')
  const [uploading, setUploading] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{role: string, content: string}>>([])
  const [uploadMessage, setUploadMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [deletingUpload, setDeletingUpload] = useState<number | null>(null)
  const [supportedTypes] = useState([
    { value: 'profile_tamu', label: 'Guest Profile Data' },
    { value: 'reservasi', label: 'Reservation Data' },
    { value: 'chat_whatsapp', label: 'WhatsApp Chat Data' },
    { value: 'transaksi_resto', label: 'Restaurant Transaction Data' },
  ])

  // Helper function to format date range
  const formatDateRange = (from: Date | null | undefined, to: Date | null | undefined, format: 'short' | 'medium' | 'long' = 'medium') => {
    if (!from || !to) return ''
    
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: format === 'short' ? 'numeric' : format === 'medium' ? 'short' : 'long',
      day: 'numeric'
    }
    
    const locale = 'id-ID' // Indonesian locale
    
    if (format === 'short') {
      // Format: DD/MM/YYYY - DD/MM/YYYY
      return `${from.getDate().toString().padStart(2, '0')}/${(from.getMonth() + 1).toString().padStart(2, '0')}/${from.getFullYear()} - ${to.getDate().toString().padStart(2, '0')}/${(to.getMonth() + 1).toString().padStart(2, '0')}/${to.getFullYear()}`
    } else {
      // Format: DD MMM YYYY - DD MMM YYYY (Indonesian)
      return `${from.toLocaleDateString(locale, options)} - ${to.toLocaleDateString(locale, options)}`
    }
  }

  // Analytics state
  const today = new Date()
  const defaultEnd = today.toISOString().slice(0, 10)
  const defaultStart = new Date(today.getTime() - 29 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

  const [compareOn, setCompareOn] = useState(false)
  const [dimensions, setDimensions] = useState<{ segment: string[]; room_type: string[]; local_region: string[]; nationality: string[] }>({ segment: [], room_type: [], local_region: [], nationality: [] })
  
  // Function to calculate default dates based on latest depart_date
  const calculateDefaultDates = (latestDepartDate: string | null) => {
    if (latestDepartDate) {
      const endDate = new Date(latestDepartDate)
      const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000) // 7 days before
      return {
        start: startDate.toISOString().slice(0, 10),
        end: endDate.toISOString().slice(0, 10)
      }
    } else {
      // Fallback to current date - 7 days
      const endDate = new Date()
      const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
      return {
        start: startDate.toISOString().slice(0, 10),
        end: endDate.toISOString().slice(0, 10)
      }
    }
  }

  const [panelA, setPanelA] = useState<PanelState>({
    dateRange: { from: new Date(defaultStart), to: new Date(defaultEnd) },
    group_by: 'segment',
    segmentSelected: '',
    roomTypeSelected: '',
    localRegionSelected: '',
    nationalitySelected: '',
    topN: 6,
    includeOther: true,
    totalRooms: 94,
    data: null,
    loading: false,
    error: null,
  })
  const [panelB, setPanelB] = useState<PanelState>({
    dateRange: { from: new Date(defaultStart), to: new Date(defaultEnd) },
    group_by: 'segment',
    segmentSelected: '',
    roomTypeSelected: '',
    localRegionSelected: '',
    nationalitySelected: '',
    topN: 6,
    includeOther: true,
    totalRooms: 94,
    data: null,
    loading: false,
    error: null,
  })

  const API_BASE = process.env.API_BASE || 'http://localhost:8000'

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, uploadsRes] = await Promise.all([
        axios.get(`${API_BASE}/dashboard/stats`),
        axios.get(`${API_BASE}/dashboard/recent-uploads`)
      ])
      setStats(statsRes.data)
      setRecentUploads(uploadsRes.data)
      
      // Update default date range based on latest depart_date
      if (statsRes.data.latest_depart_date) {
        const defaultDates = calculateDefaultDates(statsRes.data.latest_depart_date)
        const newDateRange = { 
          from: new Date(defaultDates.start), 
          to: new Date(defaultDates.end) 
        }
        
        setPanelA(prev => ({ ...prev, dateRange: newDateRange }))
        setPanelB(prev => ({ ...prev, dateRange: newDateRange }))
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    }
  }

  const fetchDimensions = async () => {
    try {
      if (!panelA.dateRange?.from || !panelA.dateRange?.to) return
      const res = await axios.get(`${API_BASE}/analytics/dimensions`, { 
        params: { 
          start: panelA.dateRange.from.toISOString().slice(0, 10), 
          end: panelA.dateRange.to.toISOString().slice(0, 10) 
        } 
      })
      setDimensions(res.data)
    } catch (e) {
      console.error('Failed to fetch dimensions', e)
    }
  }

  useEffect(() => {
    fetchDimensions()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [panelA.dateRange])

  const fetchAnalytics = async (panel: 'A' | 'B') => {
    const ps = panel === 'A' ? panelA : panelB
    const setPs = panel === 'A' ? setPanelA : setPanelB
    try {
      if (!ps.dateRange?.from || !ps.dateRange?.to) return
      setPs(prev => ({ ...prev, loading: true, error: null }))
      const params: Record<string, string> = {
        start: ps.dateRange.from.toISOString().slice(0, 10),
        end: ps.dateRange.to.toISOString().slice(0, 10),
        group_by: ps.group_by,
      }
      if (ps.segmentSelected) params['segment_in'] = ps.segmentSelected
      if (ps.roomTypeSelected) params['room_type_in'] = ps.roomTypeSelected
      if (ps.localRegionSelected) params['local_region_in'] = ps.localRegionSelected
      if (ps.nationalitySelected) params['nationality_in'] = ps.nationalitySelected
      if (ps.topN) params['top_n'] = String(ps.topN)
      if (ps.includeOther) params['include_other'] = 'true'

      const res = await axios.get<AnalyticsResponse>(`${API_BASE}/analytics/aggregate`, { params })
      setPs(prev => ({ ...prev, data: res.data, loading: false }))
    } catch (e: any) {
      setPs(prev => ({ ...prev, error: e?.response?.data?.detail || 'Failed to fetch analytics', loading: false }))
    }
  }

  const formatCurrency = (n: number | undefined | null) => {
    const v = typeof n === 'number' ? n : 0
    return v.toLocaleString('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })
  }

  const computeOccupancyPct = (data: AnalyticsResponse | null, totalRooms: number) => {
    if (!data || !data.totals || !totalRooms || totalRooms <= 0) return 0
    const nights = data.totals.occupied_room_nights || 0
    const days = data.period.days || 1
    const denom = totalRooms * days
    if (denom <= 0) return 0
    return Math.min(100, (nights / denom) * 100)
  }

  const handleFileUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    setUploadMessage(null)
    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('file_type', selectedFileType)

    // Debug logging
    console.log('Uploading file:', selectedFile.name)
    console.log('File type:', selectedFileType)
    console.log('FormData entries:')
    Array.from(formData.entries()).forEach(([key, value]) => {
      console.log(key, value)
    })

    try {
      const response = await axios.post(`${API_BASE}/csv/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setUploadMessage({
        type: 'success',
        text: `File uploaded successfully! ${response.data.rows_processed} rows processed (${response.data.rows_inserted} new, ${response.data.rows_updated} updated).`
      })
      setSelectedFile(null)
      fetchDashboardData() // Refresh data
      fetchDimensions() // Refresh dimensions for analytics
      
      // Clear success message after 5 seconds
      setTimeout(() => setUploadMessage(null), 5000)
    } catch (error: any) {
      console.error('Upload error:', error)
      setUploadMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Upload failed. Please try again.'
      })
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteUpload = async (uploadId: number) => {
    if (!confirm('Are you sure you want to delete this upload? This will remove all data from this file and re-process the database.')) {
      return
    }

    setDeletingUpload(uploadId)
    try {
      await axios.delete(`${API_BASE}/dashboard/upload/${uploadId}`)
      setUploadMessage({
        type: 'success',
        text: 'Upload deleted successfully and database re-processed!'
      })
      fetchDashboardData() // Refresh data
      
      // Clear success message after 5 seconds
      setTimeout(() => setUploadMessage(null), 5000)
    } catch (error: any) {
      console.error('Delete error:', error)
      setUploadMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Delete failed. Please try again.'
      })
    } finally {
      setDeletingUpload(null)
    }
  }

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatMessage.trim()) return

    const userMessage = { role: 'user', content: chatMessage }
    setChatHistory(prev => [...prev, userMessage])
    setChatMessage('')

    // TODO: Integrate with AI service
    const botResponse = { role: 'assistant', content: 'This is a placeholder response. AI integration coming soon!' }
    setChatHistory(prev => [...prev, botResponse])
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">DashAgent</h1>
            <div className="flex items-center gap-3">
              <Button onClick={() => setIsUploadModalOpen(true)} variant="outline" className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Data
              </Button>
            <Button onClick={() => setIsChatbotOpen(true)} className="flex items-center gap-2">
              <Bot className="w-5 h-5" />
              Chat with AI
            </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Guests</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.total_guests || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Calendar className="w-8 h-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Reservations</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.total_reservations || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <MessageCircle className="w-8 h-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Chats</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.total_chats || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>



        {/* Analytics Panel */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Analytics Dashboard
            </CardTitle>
            {/* Compare Mode Toggle */}
              <div className="flex items-center gap-3">
                <Switch
                  id="compareToggle"
                  checked={compareOn}
                  onCheckedChange={setCompareOn}
                />
                <label htmlFor="compareToggle" className="text-sm font-medium text-gray-700">
                  Enable Compare Mode
                </label>
              </div>
          </CardHeader>
          <CardContent>

            {/* Controls */}
            {compareOn ? (
              <ResizablePanelGroup direction="horizontal" className="min-h-[600px] rounded-lg border">
                {/* Panel A Controls */}
                <ResizablePanel defaultSize={50} minSize={30}>
                  <div className="p-4">
                <h3 className="font-semibold mb-2">Panel A</h3>
                <div className="mb-4">
                  <label className="text-sm text-gray-600 mb-2 block">Date Range</label>
                  <DateRangePicker
                    dateRange={panelA.dateRange}
                    onDateRangeChange={(range) => setPanelA(p => ({...p, dateRange: range}))}
                    placeholder="Select date range for Panel A"
                  />
                </div>
                {/* Advanced Filters Accordion */}
                <Accordion type="single" collapsible className="w-full mb-4">
                  <AccordionItem value="filters">
                    <AccordionTrigger className="text-sm font-medium">
                      Advanced Filters & Dimensions
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div>
                        <label className="text-sm text-gray-600 font-medium">Group By</label>
                        <select value={panelA.group_by} onChange={e => setPanelA(p => ({...p, group_by: e.target.value as GroupBy}))} className="w-full border rounded px-2 py-1 mt-1">
                          <option value="none">None</option>
                          <option value="segment">Segment</option>
                          <option value="room_type">Room Type</option>
                          <option value="local_region">City (local_region)</option>
                          <option value="nationality">Nationality</option>
                          <option value="age_group">Age Group</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select segments</label>
                        <MultiSelect
                          options={dimensions.segment}
                          selected={panelA.segmentSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, segmentSelected: selected.join(',')}))}
                          placeholder="Select segments..."
                          searchPlaceholder="Search segments..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select room types</label>
                        <MultiSelect
                          options={dimensions.room_type}
                          selected={panelA.roomTypeSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, roomTypeSelected: selected.join(',')}))}
                          placeholder="Select room types..."
                          searchPlaceholder="Search room types..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select cities</label>
                        <MultiSelect
                          options={dimensions.local_region}
                          selected={panelA.localRegionSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, localRegionSelected: selected.join(',')}))}
                          placeholder="Select cities..."
                          searchPlaceholder="Search cities..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select nationalities</label>
                        <MultiSelect
                          options={dimensions.nationality}
                          selected={panelA.nationalitySelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, nationalitySelected: selected.join(',')}))}
                          placeholder="Select nationalities..."
                          searchPlaceholder="Search nationalities..."
                          className="mt-1"
                        />
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="options">
                    <AccordionTrigger className="text-sm font-medium">
                      Display Options & Settings
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-gray-600 font-medium">Top N</label>
                          <input type="number" min={1} max={50} value={panelA.topN || 6} onChange={e => setPanelA(p => ({...p, topN: Number(e.target.value)}))} className="w-full border rounded px-2 py-1 mt-1" />
                        </div>
                        <div>
                          <label className="text-sm text-gray-600 font-medium">Total Rooms</label>
                          <input type="number" min={1} value={panelA.totalRooms} onChange={e => setPanelA(p => ({...p, totalRooms: Number(e.target.value)}))} className="w-full border rounded px-2 py-1 mt-1" />
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <input id="includeOtherA" type="checkbox" checked={panelA.includeOther} onChange={e => setPanelA(p => ({...p, includeOther: e.target.checked}))} />
                        <label htmlFor="includeOtherA" className="text-sm text-gray-600">Include Other</label>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
                    <div className="flex gap-2 mb-4">
                      <Button onClick={() => fetchAnalytics('A')}>{panelA.loading ? 'Loading…' : 'Apply A'}</Button>
                      {panelA.error && <span className="text-red-600 text-sm">{panelA.error}</span>}
                    </div>

                    {/* Panel A Results */}
                    <div className="border-t pt-4">
                      <h4 className="font-semibold mb-4">Results</h4>
                      {panelA.data ? (
                        <>
                          {/* Revenue Section */}
                          <div className="mb-6">
                            <div className="text-center p-4 bg-blue-50 rounded-lg mb-4">
                              <div className="text-2xl font-bold text-blue-600">{formatCurrency(panelA.data.totals.revenue_sum)}</div>
                              <div className="text-sm text-gray-600">Total Revenue</div>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDateRange(panelA.dateRange?.from, panelA.dateRange?.to, 'medium')}
                              </div>
                            </div>
                            <PieChartContainer
                              data={panelA.data.breakdown}
                              dataKey="revenue_sum"
                              nameKey="key"
                              title="Revenue Breakdown"
                              description={`By ${panelA.group_by}`}
                              className="min-h-[300px]"
                            />
                          </div>

                          {/* Occupancy Section */}
                          <div className="mb-6">
                            <div className="text-center p-4 bg-green-50 rounded-lg mb-4">
                              <div className="text-2xl font-bold text-green-600">{computeOccupancyPct(panelA.data, panelA.totalRooms).toFixed(1)}%</div>
                              <div className="text-sm text-gray-600">Occupancy Rate</div>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDateRange(panelA.dateRange?.from, panelA.dateRange?.to, 'medium')}
                              </div>
                            </div>
                            <PieChartContainer
                              data={panelA.data.breakdown}
                              dataKey="occupied_room_nights"
                              nameKey="key"
                              title="Occupancy Breakdown"
                              description={`By ${panelA.group_by}`}
                              className="min-h-[300px]"
                            />
                          </div>

                          {/* ARR Section */}
                          <div className="mb-6">
                            <div className="text-center p-4 bg-purple-50 rounded-lg mb-4">
                              <div className="text-2xl font-bold text-purple-600">{formatCurrency(panelA.data.totals.arr_simple)}</div>
                              <div className="text-sm text-gray-600">Average Room Rate</div>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDateRange(panelA.dateRange?.from, panelA.dateRange?.to, 'medium')}
                              </div>
                            </div>
                            <PieChartContainer
                              data={panelA.data.breakdown}
                              dataKey="arr_simple"
                              nameKey="key"
                              title="ARR Breakdown"
                              description={`By ${panelA.group_by}`}
                              className="min-h-[300px]"
                            />
                          </div>
                        </>
                      ) : (
                        <div className="text-sm text-gray-500">No data. Click Apply A to load analytics.</div>
                      )}
                    </div>
                  </div>
                </ResizablePanel>

                <ResizableHandle withHandle />

                {/* Panel B Controls */}
                <ResizablePanel defaultSize={50} minSize={30}>
                  <div className="p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold mb-2">Panel B</h3>
                </div>
                
                {/* Basic Settings */}
                <div className="mb-4">
                  <label className="text-sm text-gray-600 mb-2 block">Date Range</label>
                  <DateRangePicker
                    dateRange={panelB.dateRange}
                    onDateRangeChange={(range) => setPanelB(p => ({...p, dateRange: range}))}
                    placeholder="Select date range for Panel B"
                  />
                </div>

                {/* Advanced Filters Accordion */}
                <Accordion type="single" collapsible className="w-full mb-4">
                  <AccordionItem value="filters-b">
                    <AccordionTrigger className="text-sm font-medium">
                      Advanced Filters & Dimensions
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div>
                        <label className="text-sm text-gray-600 font-medium">Group By</label>
                        <select value={panelB.group_by} onChange={e => setPanelB(p => ({...p, group_by: e.target.value as GroupBy}))} className="w-full border rounded px-2 py-1 mt-1">
                          <option value="none">None</option>
                          <option value="segment">Segment</option>
                          <option value="room_type">Room Type</option>
                          <option value="local_region">City (local_region)</option>
                          <option value="nationality">Nationality</option>
                          <option value="age_group">Age Group</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select segments</label>
                        <MultiSelect
                          options={dimensions.segment}
                          selected={panelB.segmentSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelB(p => ({...p, segmentSelected: selected.join(',')}))}
                          placeholder="Select segments..."
                          searchPlaceholder="Search segments..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select room types</label>
                        <MultiSelect
                          options={dimensions.room_type}
                          selected={panelB.roomTypeSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelB(p => ({...p, roomTypeSelected: selected.join(',')}))}
                          placeholder="Select room types..."
                          searchPlaceholder="Search room types..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select cities</label>
                        <MultiSelect
                          options={dimensions.local_region}
                          selected={panelB.localRegionSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelB(p => ({...p, localRegionSelected: selected.join(',')}))}
                          placeholder="Select cities..."
                          searchPlaceholder="Search cities..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select nationalities</label>
                        <MultiSelect
                          options={dimensions.nationality}
                          selected={panelB.nationalitySelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelB(p => ({...p, nationalitySelected: selected.join(',')}))}
                          placeholder="Select nationalities..."
                          searchPlaceholder="Search nationalities..."
                          className="mt-1"
                        />
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="options-b">
                    <AccordionTrigger className="text-sm font-medium">
                      Display Options & Settings
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-gray-600 font-medium">Top N</label>
                          <input type="number" min={1} max={50} value={panelB.topN || 6} onChange={e => setPanelB(p => ({...p, topN: Number(e.target.value)}))} className="w-full border rounded px-2 py-1 mt-1" />
                        </div>
                        <div>
                          <label className="text-sm text-gray-600 font-medium">Total Rooms</label>
                          <input type="number" min={1} value={panelB.totalRooms} onChange={e => setPanelB(p => ({...p, totalRooms: Number(e.target.value)}))} className="w-full border rounded px-2 py-1 mt-1" />
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <input id="includeOtherB" type="checkbox" checked={panelB.includeOther} onChange={e => setPanelB(p => ({...p, includeOther: e.target.checked}))} />
                        <label htmlFor="includeOtherB" className="text-sm text-gray-600">Include Other</label>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>

                    <div className="flex gap-2 mb-4">
                      <Button onClick={() => fetchAnalytics('B')} disabled={!compareOn}>{panelB.loading ? 'Loading…' : 'Apply B'}</Button>
                      {panelB.error && <span className="text-red-600 text-sm">{panelB.error}</span>}
                    </div>

                    {/* Panel B Results */}
                    <div className="border-t pt-4">
                      <h4 className="font-semibold mb-4">Results</h4>
                      {panelB.data ? (
                        <>
                          {/* Revenue Section */}
                          <div className="mb-6">
                            <div className="text-center p-4 bg-blue-50 rounded-lg mb-4">
                              <div className="text-2xl font-bold text-blue-600">{formatCurrency(panelB.data.totals.revenue_sum)}</div>
                              <div className="text-sm text-gray-600">Total Revenue</div>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDateRange(panelB.dateRange?.from, panelB.dateRange?.to, 'medium')}
                              </div>
                            </div>
                            <PieChartContainer
                              data={panelB.data.breakdown}
                              dataKey="revenue_sum"
                              nameKey="key"
                              title="Revenue Breakdown"
                              description={`By ${panelB.group_by}`}
                              className="min-h-[300px]"
                            />
                          </div>

                          {/* Occupancy Section */}
                          <div className="mb-6">
                            <div className="text-center p-4 bg-green-50 rounded-lg mb-4">
                              <div className="text-2xl font-bold text-green-600">{computeOccupancyPct(panelB.data, panelB.totalRooms).toFixed(1)}%</div>
                              <div className="text-sm text-gray-600">Occupancy Rate</div>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDateRange(panelB.dateRange?.from, panelB.dateRange?.to, 'medium')}
                              </div>
                            </div>
                            <PieChartContainer
                              data={panelB.data.breakdown}
                              dataKey="occupied_room_nights"
                              nameKey="key"
                              title="Occupancy Breakdown"
                              description={`By ${panelB.group_by}`}
                              className="min-h-[300px]"
                            />
                          </div>

                          {/* ARR Section */}
                          <div className="mb-6">
                            <div className="text-center p-4 bg-purple-50 rounded-lg mb-4">
                              <div className="text-2xl font-bold text-purple-600">{formatCurrency(panelB.data.totals.arr_simple)}</div>
                              <div className="text-sm text-gray-600">Average Room Rate</div>
                              <div className="text-xs text-gray-500 mt-1">
                                {formatDateRange(panelB.dateRange?.from, panelB.dateRange?.to, 'medium')}
                              </div>
                            </div>
                            <PieChartContainer
                              data={panelB.data.breakdown}
                              dataKey="arr_simple"
                              nameKey="key"
                              title="ARR Breakdown"
                              description={`By ${panelB.group_by}`}
                              className="min-h-[300px]"
                            />
                          </div>
                        </>
                      ) : (
                        <div className="text-sm text-gray-600">No data. Enable compare and click Apply B.</div>
                      )}
                    </div>
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>
            ) : (
              /* Single Panel A - Controls Only */
              <div>
                <h3 className="font-semibold mb-2">Panel A</h3>
                <div className="mb-4">
                  <label className="text-sm text-gray-600 mb-2 block">Date Range</label>
                  <DateRangePicker
                    dateRange={panelA.dateRange}
                    onDateRangeChange={(range) => setPanelA(p => ({...p, dateRange: range}))}
                    placeholder="Select date range for Panel A"
                  />
                </div>
                {/* Advanced Filters Accordion */}
                <Accordion type="single" collapsible className="w-full mb-4">
                  <AccordionItem value="filters">
                    <AccordionTrigger className="text-sm font-medium">
                      Advanced Filters & Dimensions
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div>
                        <label className="text-sm text-gray-600 font-medium">Group By</label>
                        <select value={panelA.group_by} onChange={e => setPanelA(p => ({...p, group_by: e.target.value as GroupBy}))} className="w-full border rounded px-2 py-1 mt-1">
                          <option value="none">None</option>
                          <option value="segment">Segment</option>
                          <option value="room_type">Room Type</option>
                          <option value="local_region">City (local_region)</option>
                          <option value="nationality">Nationality</option>
                          <option value="age_group">Age Group</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select segments</label>
                        <MultiSelect
                          options={dimensions.segment}
                          selected={panelA.segmentSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, segmentSelected: selected.join(',')}))}
                          placeholder="Select segments..."
                          searchPlaceholder="Search segments..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select room types</label>
                        <MultiSelect
                          options={dimensions.room_type}
                          selected={panelA.roomTypeSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, roomTypeSelected: selected.join(',')}))}
                          placeholder="Select room types..."
                          searchPlaceholder="Search room types..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select cities</label>
                        <MultiSelect
                          options={dimensions.local_region}
                          selected={panelA.localRegionSelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, localRegionSelected: selected.join(',')}))}
                          placeholder="Select cities..."
                          searchPlaceholder="Search cities..."
                          className="mt-1"
                        />
                      </div>

                      <div>
                        <label className="text-sm text-gray-600 font-medium">Select nationalities</label>
                        <MultiSelect
                          options={dimensions.nationality}
                          selected={panelA.nationalitySelected.split(',').filter(Boolean)}
                          onChange={(selected) => setPanelA(p => ({...p, nationalitySelected: selected.join(',')}))}
                          placeholder="Select nationalities..."
                          searchPlaceholder="Search nationalities..."
                          className="mt-1"
                        />
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="options">
                    <AccordionTrigger className="text-sm font-medium">
                      Display Options & Settings
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-gray-600 font-medium">Top N</label>
                          <input type="number" min={1} max={50} value={panelA.topN || 6} onChange={e => setPanelA(p => ({...p, topN: Number(e.target.value)}))} className="w-full border rounded px-2 py-1 mt-1" />
                        </div>
                        <div>
                          <label className="text-sm text-gray-600 font-medium">Total Rooms</label>
                          <input type="number" min={1} value={panelA.totalRooms} onChange={e => setPanelA(p => ({...p, totalRooms: Number(e.target.value)}))} className="w-full border rounded px-2 py-1 mt-1" />
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <input id="includeOtherA" type="checkbox" checked={panelA.includeOther} onChange={e => setPanelA(p => ({...p, includeOther: e.target.checked}))} />
                        <label htmlFor="includeOtherA" className="text-sm text-gray-600">Include Other</label>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>

                <div className="flex gap-2 mb-4">
                  <Button onClick={() => fetchAnalytics('A')}>{panelA.loading ? 'Loading…' : 'Apply A'}</Button>
                  {panelA.error && <span className="text-red-600 text-sm">{panelA.error}</span>}
                </div>

                {/* Panel A Results for Single Panel Mode */}
                {panelA.data && (
                  <div className="border-t pt-4">
                    <h4 className="font-semibold mb-4">Results</h4>
                    <>
                      {/* Revenue Section */}
                      <div className="mb-6">
                        <div className="text-center p-4 bg-blue-50 rounded-lg mb-4">
                          <div className="text-2xl font-bold text-blue-600">{formatCurrency(panelA.data.totals.revenue_sum)}</div>
                          <div className="text-sm text-gray-600">Total Revenue</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {formatDateRange(panelA.dateRange?.from, panelA.dateRange?.to, 'medium')}
                          </div>
                        </div>
                        <PieChartContainer
                          data={panelA.data.breakdown}
                          dataKey="revenue_sum"
                          nameKey="key"
                          title="Revenue Breakdown"
                          description={`By ${panelA.group_by}`}
                          className="min-h-[300px]"
                        />
                      </div>

                      {/* Occupancy Section */}
                      <div className="mb-6">
                        <div className="text-center p-4 bg-green-50 rounded-lg mb-4">
                          <div className="text-2xl font-bold text-green-600">{computeOccupancyPct(panelA.data, panelA.totalRooms).toFixed(1)}%</div>
                          <div className="text-sm text-gray-600">Occupancy Rate</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {formatDateRange(panelA.dateRange?.from, panelA.dateRange?.to, 'medium')}
                          </div>
                        </div>
                        <PieChartContainer
                          data={panelA.data.breakdown}
                          dataKey="occupied_room_nights"
                          nameKey="key"
                          title="Occupancy Breakdown"
                          description={`By ${panelA.group_by}`}
                          className="min-h-[300px]"
                        />
                      </div>

                      {/* ARR Section */}
                      <div className="mb-6">
                        <div className="text-center p-4 bg-purple-50 rounded-lg mb-4">
                          <div className="text-2xl font-bold text-purple-600">{formatCurrency(panelA.data.totals.arr_simple)}</div>
                          <div className="text-sm text-gray-600">Average Room Rate</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {formatDateRange(panelA.dateRange?.from, panelA.dateRange?.to, 'medium')}
                          </div>
                        </div>
                        <PieChartContainer
                          data={panelA.data.breakdown}
                          dataKey="arr_simple"
                          nameKey="key"
                          title="ARR Breakdown"
                          description={`By ${panelA.group_by}`}
                          className="min-h-[300px]"
                        />
                      </div>
                    </>
                  </div>
                )}
              </div>
            )}

          </CardContent>
        </Card>
      </main>

      {/* Chatbot Modal */}
      <Dialog open={isChatbotOpen} onOpenChange={setIsChatbotOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>AI Assistant</DialogTitle>
            <Button
              onClick={() => setIsChatbotOpen(false)}
              className="absolute right-4 top-4"
            >
              <X className="w-4 h-4" />
            </Button>
          </DialogHeader>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {chatHistory.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input */}
          <div className="p-6 border-t">
            <form onSubmit={handleChatSubmit} className="flex gap-2">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Ask me anything about your hotel data..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Button type="submit">
                Send
              </Button>
            </form>
          </div>
        </DialogContent>
      </Dialog>

      {/* Upload Modal */}
      <Dialog open={isUploadModalOpen} onOpenChange={setIsUploadModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Data Upload Manager
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Upload Area */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Upload New Data</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Drag and drop your CSV file here, or click to browse</p>
                
                {/* File Type Selection */}
                <div className="mb-4">
                  <label htmlFor="file-type" className="block text-sm font-medium text-gray-700 mb-2">
                    Select File Type:
                  </label>
                  <select
                    id="file-type"
                    value={selectedFileType}
                    onChange={(e) => setSelectedFileType(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {supportedTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="inline-block">
                  <Button asChild>
                    <span>Choose File</span>
                  </Button>
                </label>
                
                {selectedFile && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-600">Selected: {selectedFile.name}</p>
                    <p className="text-sm text-gray-500">Type: {supportedTypes.find(t => t.value === selectedFileType)?.label}</p>
                    <Button 
                      onClick={handleFileUpload}
                      disabled={uploading}
                      className="mt-2"
                    >
                      {uploading ? 'Uploading...' : 'Upload'}
                    </Button>
                  </div>
                )}

                {/* Upload Message */}
                {uploadMessage && (
                  <div className={`mt-4 p-3 rounded-md ${
                    uploadMessage.type === 'success' 
                      ? 'bg-green-50 text-green-800 border border-green-200' 
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    {uploadMessage.text}
                  </div>
                )}
              </div>
            </div>

            {/* Recent Uploads */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Recent Uploads</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rows</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {recentUploads.map((upload) => (
                      <tr key={upload.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{upload.filename}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{upload.file_type}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            upload.status === 'completed' ? 'bg-green-100 text-green-800' :
                            upload.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {upload.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{upload.rows_processed}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(upload.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <Button
                            onClick={() => handleDeleteUpload(upload.id)}
                            disabled={deletingUpload === upload.id}
                            variant="destructive"
                            size="sm"
                            className="flex items-center gap-1"
                          >
                            <Trash2 className="w-4 h-4" />
                            {deletingUpload === upload.id ? 'Deleting...' : 'Delete'}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
