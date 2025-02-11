"use client";

import { useState } from "react";
import { Upload, Loader2, File } from "lucide-react";
import { motion } from "framer-motion";
import { NEXT_PUBLIC_API_BASE_URL } from "@/app/config";

export default function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.type === "application/pdf") {
      setFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);

    try {
      const response = await fetch(NEXT_PUBLIC_API_BASE_URL + "/upload/", {
        method: "POST",
        body: formData,
        // credentials: 'include'
      });

      if(!response.ok) {
        const errorText = await response.text(); // Get text of error response
        throw new Error(`Upload failed with status ${response.status}: ${errorText}`);
      }

      const data = await response.json(); // Try to parse JSON
      console.log("Upload response data:", data); // Log successful response data

      if (!response.ok) throw new Error("Upload failed");

      setFile(null);
      // You might want to use a proper toast notification here
      alert("Document uploaded successfully!");
    } catch (error) {
      console.error("Upload error:", error);
      alert("Error uploading document");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-950/50"
            : "border-gray-300 dark:border-gray-700"
        } dark:bg-gray-800`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
          disabled={uploading}
        />

        <label
          htmlFor="file-upload"
          className="cursor-pointer flex flex-col items-center gap-2"
        >
          <Upload className="w-12 h-12 text-gray-400 dark:text-gray-500" />
          <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
            Drag and drop your PDF here, or click to select
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Only PDF files are supported
          </p>
        </label>

        {file && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg flex items-center gap-2"
          >
            <File className="w-5 h-5 text-blue-500" />
            <span className="flex-1 truncate dark:text-gray-100">
              {file.name}
            </span>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload
                </>
              )}
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
