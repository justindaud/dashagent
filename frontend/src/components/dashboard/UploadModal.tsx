"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Upload, Trash2 } from "lucide-react";
import { RecentUpload } from "@/lib/types";

interface UploadModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onUploadSuccess: () => void;
}

export function UploadModal({ isOpen, onOpenChange, onUploadSuccess }: UploadModalProps) {
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [loadingUploads, setLoadingUploads] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileType, setSelectedFileType] = useState<string>("profile_tamu");
  const [uploading, setUploading] = useState(false);
  const [deletingUploadId, setDeletingUploadId] = useState<number | null>(null);
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const supportedTypes = [
    { value: "profile_tamu", label: "Guest Profile Data" },
    { value: "reservasi", label: "Reservation Data" },
    { value: "chat_whatsapp", label: "WhatsApp Chat Data" },
    { value: "transaksi_resto", label: "Restaurant Transaction Data" },
  ];

  const fetchRecentUploads = async () => {
    setLoadingUploads(true);
    try {
      const res = await axios.get(`${API_BASE}/dashboard/recent-uploads`, { withCredentials: true });

      const responseBody = res.data;
      let uploads: RecentUpload[] = [];

      if (responseBody && Array.isArray(responseBody.data)) {
        uploads = responseBody.data;
      } else if (Array.isArray(responseBody)) {
        uploads = responseBody;
      }

      setRecentUploads(uploads);
    } catch (error) {
      console.error("Error fetching recent uploads:", error);
      setRecentUploads([]);
    } finally {
      setLoadingUploads(false);
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
        withCredentials: true,
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

  const confirmDelete = (uploadId: number) => {
    setDeletingUploadId(uploadId);
    setIsAlertOpen(true);
  };

  const handleDeleteUpload = async () => {
    if (!deletingUploadId) return;
    try {
      await axios.delete(`${API_BASE}/dashboard/upload/${deletingUploadId}`);
      setUploadMessage({ type: "success", text: "Delete success and data re-processed!" });
      fetchRecentUploads();
      onUploadSuccess();
    } catch (error: any) {
      setUploadMessage({ type: "error", text: error.response?.data?.detail || "Delete failed." });
    } finally {
      setDeletingUploadId(null);
    }
  };

  return (
    <>
      <Dialog
        open={isOpen}
        onOpenChange={(val) => {
          if (uploading && !val) return;
          onOpenChange(val);
        }}
      >
        <DialogContent
          className={`max-w-md md:max-w-2xl lg:max-w-4xl max-h-[90vh] flex flex-col ${uploading ? "[&>button]:hidden" : ""}`}
          onInteractOutside={(e) => {
            if (uploading) {
              e.preventDefault();
            }
          }}
          onEscapeKeyDown={(e) => {
            if (uploading) {
              e.preventDefault();
            }
          }}
        >
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {uploading ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" /> : <Upload className="w-5 h-5" />}
              Data Upload Manager
            </DialogTitle>
            {uploading && <p className="text-sm text-muted-foreground text-red-500 font-medium mt-1">Uploading file...</p>}
          </DialogHeader>
          <div className="flex-grow overflow-y-auto pr-2 space-y-6 p-1">
            {/* Area Upload */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Upload New Data</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input type="file" accept=".csv" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} className="hidden" id="file-upload" />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">Drag & drop file or click to browse</p>
                </label>

                <Select value={selectedFileType} onValueChange={setSelectedFileType}>
                  <SelectTrigger className="w-full max-w-xs mx-auto">
                    <SelectValue placeholder="Select data type" />
                  </SelectTrigger>
                  <SelectContent>
                    {supportedTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {selectedFile && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-600">Selected: {selectedFile.name}</p>
                    {uploading ? (
                      <div className="mt-2 space-y-2">
                        <p className="text-sm text-primary">Uploading File...</p>
                      </div>
                    ) : (
                      <Button onClick={handleFileUpload} disabled={uploading} className="mt-2">
                        Upload File
                      </Button>
                    )}
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
              {loadingUploads ? (
                <div className="space-y-2">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : (
                <>
                  {/* Tampilan Tabel untuk Desktop */}
                  <div className="hidden md:block border rounded-lg overflow-x-auto">
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
                              <Button onClick={() => confirmDelete(upload.id)} disabled={!!deletingUploadId} variant="destructive" size="sm">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Tampilan Kartu untuk Mobile */}
                  <div className="md:hidden space-y-4">
                    {recentUploads.map((upload) => (
                      <div key={upload.id} className="border rounded-lg p-4 space-y-2">
                        <div className="font-medium text-gray-900 truncate">{upload.filename}</div>
                        <div className="text-sm text-gray-500">
                          <span className="font-medium text-gray-700">Type:</span> {upload.file_type}
                        </div>
                        <div className="text-sm text-gray-500">
                          <span className="font-medium text-gray-700">Date:</span> {new Date(upload.created_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center justify-between pt-2">
                          <span
                            className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              upload.status === "completed" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                            }`}
                          >
                            {upload.status}
                          </span>
                          <Button onClick={() => confirmDelete(upload.id)} disabled={!!deletingUploadId} variant="destructive" size="sm">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog Konfirmasi Hapus */}
      <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the upload record and all associated guest/reservation data from the
              database.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeletingUploadId(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUpload}>Continue</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
