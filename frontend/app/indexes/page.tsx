"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";
import { getHistory } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { Navbar } from "@/components/Navbar";
import { Card } from "@/components/ui/card";

function HistoryList() {
  const ready = useRequireAuth();
  const params = useSearchParams();
  const documentId = params.get("document");

  const { data = [], isLoading } = useQuery({
    queryKey: ["history", documentId],
    queryFn: () => getHistory(documentId ? Number(documentId) : undefined),
    enabled: ready,
  });

  if (!ready) return null;

  return (
    <main className="mx-auto max-w-3xl space-y-4 px-4 py-8">
      <h1 className="flex items-center gap-2 text-2xl font-bold">
        <History className="h-6 w-6 text-primary" /> Version history
      </h1>
      {isLoading ? (
        <p className="text-muted">Loading…</p>
      ) : data.length === 0 ? (
        <p className="text-muted">No indexes generated yet.</p>
      ) : (
        data.map((idx) => (
          <Link key={idx.id} href={`/indexes/${idx.id}`}>
            <Card className="flex items-center justify-between transition hover:border-primary">
              <div>
                <div className="font-medium">Version {idx.version}</div>
                <div className="text-sm text-muted">
                  {idx.index.total_topics} topics ·{" "}
                  {new Date(idx.created_at).toLocaleString()}
                </div>
              </div>
              <span className="text-sm text-primary">View →</span>
            </Card>
          </Link>
        ))
      )}
    </main>
  );
}

export default function HistoryPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Suspense fallback={null}>
        <HistoryList />
      </Suspense>
    </div>
  );
}
