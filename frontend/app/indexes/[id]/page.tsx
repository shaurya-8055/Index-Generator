"use client";

import { use, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Search } from "lucide-react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { downloadExport, getIndex, searchIndex } from "@/lib/api";
import type { IndexEntry } from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

const FORMATS = ["pdf", "csv", "json", "markdown"] as const;

export default function IndexViewerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const indexId = Number(id);
  const ready = useRequireAuth();
  const [query, setQuery] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["index", indexId],
    queryFn: () => getIndex(indexId),
    enabled: ready,
  });

  const { data: search } = useQuery({
    queryKey: ["search", indexId, query],
    queryFn: () => searchIndex(indexId, query),
    enabled: ready && query.trim().length > 0,
  });

  const topTopics = useMemo(() => {
    if (!data) return [];
    const entries: IndexEntry[] = data.index.groups.flatMap((g) => g.entries);
    return entries
      .map((e) => ({ topic: e.topic, count: e.pages.length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [data]);

  if (!ready) return null;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        {isLoading || !data ? (
          <p className="text-muted">Loading index…</p>
        ) : (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold">Index</h1>
                <p className="text-muted">
                  Version {data.version} ·{" "}
                  {new Date(data.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {FORMATS.map((fmt) => (
                  <Button
                    key={fmt}
                    variant="outline"
                    size="sm"
                    onClick={() => downloadExport(fmt, indexId)}
                  >
                    <Download className="h-4 w-4" /> {fmt.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="grid gap-3 sm:grid-cols-3">
              <Stat label="Topics" value={data.index.total_topics} />
              <Stat
                label="Pages referenced"
                value={data.index.total_pages_referenced}
              />
              <Stat label="Letter groups" value={data.index.groups.length} />
            </div>

            {/* Search */}
            <Card>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                <Input
                  className="pl-9"
                  placeholder="Search topics…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              {query.trim() && (
                <div className="mt-3 space-y-1">
                  {search?.results.length ? (
                    search.results.map((r) => (
                      <Row key={r.topic} topic={r.topic} pages={r.pages} />
                    ))
                  ) : (
                    <p className="text-sm text-muted">No matches.</p>
                  )}
                </div>
              )}
            </Card>

            {/* Analytics chart */}
            {topTopics.length > 0 && (
              <Card>
                <h2 className="mb-3 font-semibold">Most referenced topics</h2>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={topTopics} layout="vertical" margin={{ left: 20 }}>
                    <XAxis type="number" allowDecimals={false} hide />
                    <YAxis
                      type="category"
                      dataKey="topic"
                      width={140}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip />
                    <Bar dataKey="count" fill="var(--primary)" radius={4} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}

            {/* The index itself */}
            <Card>
              {data.index.groups.map((group) => (
                <div key={group.letter} className="mb-5">
                  <h3 className="mb-2 text-lg font-bold text-primary">
                    {group.letter}
                  </h3>
                  <div className="space-y-1">
                    {group.entries.map((entry) => (
                      <Row
                        key={entry.topic}
                        topic={entry.topic}
                        pages={entry.pages}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card className="text-center">
      <div className="text-3xl font-bold text-primary">{value}</div>
      <div className="text-sm text-muted">{label}</div>
    </Card>
  );
}

function Row({ topic, pages }: { topic: string; pages: number[] }) {
  return (
    <div className="flex items-baseline gap-2 text-sm">
      <span className="font-medium">{topic}</span>
      <span className="min-w-0 flex-1 translate-y-[-3px] border-b border-dotted border-border" />
      <span className="text-muted">{pages.join(", ")}</span>
    </div>
  );
}
