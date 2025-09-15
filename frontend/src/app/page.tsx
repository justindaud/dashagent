
"use client";

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
  )
}
