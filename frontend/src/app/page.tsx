'use client'

import { useState, useEffect } from 'react'
import { Upload, Users, Calendar, MessageCircle, CreditCard, Bot, X, Trash2 } from 'lucide-react'
import axios from 'axios'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

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

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([])
  const [isChatbotOpen, setIsChatbotOpen] = useState(false)
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
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    }
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
            <Button onClick={() => setIsChatbotOpen(true)} className="flex items-center gap-2">
              <Bot className="w-5 h-5" />
              Chat with AI
            </Button>
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

        {/* Upload Area */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Upload New Data</CardTitle>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>

        {/* Recent Uploads */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Uploads</CardTitle>
          </CardHeader>
          <CardContent>
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
    </div>
  )
}
