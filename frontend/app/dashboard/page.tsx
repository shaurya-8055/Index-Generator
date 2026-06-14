"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Loader2,
  Sparkles,
  Trash2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  deleteDocument,
  generateIndex,
  listDocuments,
} from "@/lib/api";
import type { DocumentItem } from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { Navbar } from "@/components/Navbar";
import { UploadZone } from "@/components/UploadZone";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const qc = useQueryClient();

  const { data: docs = [], isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    enabled: ready,
  });

  const generate = useMutation({
    mutationFn: (id: number) => generateIndex(id),
    onSuccess: (index) => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Index generated!");
      router.push(`/indexes/${index.id}`);
    },
    onError: (err: any) =>
      toast.error(err.response?.data?.detail ?? "Generation failed"),
  });

  const remove = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });

  if (!ready) return null;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
        <section>
          <h1 className="mb-1 text-2xl font-bold">Dashboard</h1>
          <p className="text-muted">
            Upload a document and generate a book-style index.
          </p>
        </section>

        <UploadZone
          onUploaded={() => qc.invalidateQueries({ queryKey: ["documents"] })}
        />

        <section>
          <CardTitle className="mb-3">Your documents</CardTitle>
          {isLoading ? (
            <div className="flex items-center gap-2 text-muted">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : docs.length === 0 ? (
            <p className="text-muted">No documents yet. Upload one above.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {docs.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  generating={generate.isPending && generate.variables === doc.id}
                  onGenerate={() => generate.mutate(doc.id)}
                  onDelete={() => remove.mutate(doc.id)}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function DocumentCard({
  doc,
  generating,
  onGenerate,
  onDelete,
}: {
  doc: DocumentItem;
  generating: boolean;
  onGenerate: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileText className="h-5 w-5 shrink-0 text-primary" />
          <span className="truncate font-medium" title={doc.filename}>
            {doc.filename}
          </span>
        </div>
        <button
          onClick={onDelete}
          className="text-muted hover:text-red-500"
          aria-label="Delete"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      <StatusBadge status={doc.status} pageCount={doc.page_count} />

      <div className="mt-auto flex gap-2">
        <Button size="sm" onClick={onGenerate} disabled={generating} className="flex-1">
          {generating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {generating ? "Generating…" : "Generate index"}
        </Button>
        {doc.status === "completed" && (
          <Link href={`/indexes?document=${doc.id}`}>
            <Button size="sm" variant="outline">
              History
            </Button>
          </Link>
        )}
      </div>
    </Card>
  );
}

function StatusBadge({
  status,
  pageCount,
}: {
  status: DocumentItem["status"];
  pageCount: number;
}) {
  const map = {
    uploaded: { icon: FileText, text: "Uploaded", cls: "text-muted" },
    processing: { icon: Loader2, text: "Processing", cls: "text-amber-500" },
    completed: {
      icon: CheckCircle2,
      text: `Indexed · ${pageCount} pages`,
      cls: "text-green-500",
    },
    failed: { icon: AlertCircle, text: "Failed", cls: "text-red-500" },
  }[status];
  const Icon = map.icon;
  return (
    <div className={`flex items-center gap-1.5 text-sm ${map.cls}`}>
      <Icon className={`h-4 w-4 ${status === "processing" ? "animate-spin" : ""}`} />
      {map.text}
    </div>
  );
}
