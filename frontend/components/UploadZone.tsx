"use client";

import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { uploadDocument } from "@/lib/api";
import { Card } from "./ui/card";

const ACCEPT = ".pdf,.docx,.txt,.md,.markdown";

export function UploadZone({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);

  async function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setProgress(0);
    try {
      await uploadDocument(file, setProgress);
      toast.success(`Uploaded ${file.name}`);
      onUploaded();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? "Upload failed");
    } finally {
      setProgress(null);
    }
  }

  return (
    <Card
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 border-2 border-dashed py-10 text-center transition ${
        dragging ? "border-primary bg-primary/5" : "border-border"
      }`}
    >
      <UploadCloud className="h-8 w-8 text-primary" />
      <p className="font-medium">Drag &amp; drop a document, or click to browse</p>
      <p className="text-sm text-muted">PDF, DOCX, TXT or Markdown · up to 50 MB</p>
      {progress !== null && (
        <div className="mt-3 h-2 w-48 overflow-hidden rounded-full bg-border">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </Card>
  );
}
