"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Upload, Trash2 } from "lucide-react";
import { RecentUpload } from "@/lib/types";

interface UploadModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onUploadSuccess: () => void;
}

export function UploadModal({ isOpen, onOpenChange, onUploadSuccess }: UploadModalProps) {
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileType, setSelectedFileType] = useState<string>("profile_tamu");
  const [uploading, setUploading] = useState(false);
  const [deletingUpload, setDeletingUpload] = useState<number | null>(null);
  const [uploadMessage, setUploadMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const supportedTypes = [
    { value: "profile_tamu", label: "Guest Profile Data" },
    { value: "reservasi", label: "Reservation Data" },
    { value: "chat_whatsapp", label: "WhatsApp Chat Data" },
    { value: "transaksi_resto", label: "Restaurant Transaction Data" },
  ];

  const fetchRecentUploads = async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/recent-uploads`);
      setRecentUploads(res.data);
    } catch (error) {
      console.error("Error fetching recent uploads:", error);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchRecentUploads();
    }
  }, [isOpen]);

  const handleFileUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadMessage(null);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("file_type", selectedFileType);

    try {
      const response = await axios.post(`${API_BASE}/csv/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadMessage({ type: "success", text: `Upload success! ${response.data.rows_processed} rows processed.` });
      setSelectedFile(null);
      fetchRecentUploads();
      onUploadSuccess();
    } catch (error: any) {
      setUploadMessage({ type: "error", text: error.response?.data?.detail || "Upload failed." });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteUpload = async (uploadId: number) => {
    if (!confirm("Are you sure? This will delete all associated data.")) return;
    setDeletingUpload(uploadId);
    try {
      await axios.delete(`${API_BASE}/dashboard/upload/${uploadId}`);
      setUploadMessage({ type: "success", text: "Delete success and data re-processed!" });
      fetchRecentUploads();
      onUploadSuccess();
    } catch (error: any) {
      setUploadMessage({ type: "error", text: error.response?.data?.detail || "Delete failed." });
    } finally {
      setDeletingUpload(null);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Data Upload Manager
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 p-6">
          {/* Area Upload */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Upload New Data</h3>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input type="file" accept=".csv" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} className="hidden" id="file-upload" />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Drag & drop file or click to browse</p>
              </label>

              <select
                value={selectedFileType}
                onChange={(e) => setSelectedFileType(e.target.value)}
                className="block w-full max-w-xs mx-auto px-3 py-2 border border-gray-300 rounded-md shadow-sm"
              >
                {supportedTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>

              {selectedFile && (
                <div className="mt-4">
                  <p className="text-sm text-gray-600">Selected: {selectedFile.name}</p>
                  <Button onClick={handleFileUpload} disabled={uploading} className="mt-2">
                    {uploading ? "Uploading..." : "Upload File"}
                  </Button>
                </div>
              )}
            </div>
            {uploadMessage && (
              <div
                className={`mt-4 p-3 rounded-md text-sm ${
                  uploadMessage.type === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                }`}
              >
                {uploadMessage.text}
              </div>
            )}
          </div>

          {/* Tabel Upload Terbaru */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Recent Uploads</h3>
            <div className="overflow-x-auto border rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentUploads.map((upload) => (
                    <tr key={upload.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{upload.filename}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{upload.file_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            upload.status === "completed" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {upload.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(upload.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Button onClick={() => handleDeleteUpload(upload.id)} disabled={deletingUpload === upload.id} variant="destructive" size="sm">
                          <Trash2 className="w-4 h-4" />
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
  );
}
