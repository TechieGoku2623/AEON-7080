"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function DataPage() {
  const token = useToken();
  const [rows, setRows] = useState<{ id: string; name: string; rows: number; label: string; version: number }[]>([]);

  useEffect(() => {
    if (!token) return;
    api<{ datasets: typeof rows }>("/api/data", token).then((payload) => setRows(payload.datasets)).catch(() => setRows([]));
  }, [token]);

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <Label>User data lab</Label>
          <h1 className="font-serif text-4xl">My datasets</h1>
        </div>
        <Link href="/data/upload" className="rounded-md bg-cyan px-3 py-2 text-sm text-ink">Upload data</Link>
      </div>
      <div className="grid gap-3">
        {rows.map((row) => (
          <Link key={row.id} href={`/data/${row.id}`}>
            <Panel className="flex items-center justify-between">
              <div>
                <h2 className="font-serif text-2xl">{row.name}</h2>
                <p className="font-mono text-xs text-mute">v{row.version} · {row.label}</p>
              </div>
              <p className="font-mono text-sm">{row.rows.toLocaleString()} rows</p>
            </Panel>
          </Link>
        ))}
        {rows.length === 0 && <p className="text-mute">No datasets yet.</p>}
      </div>
    </div>
  );
}
