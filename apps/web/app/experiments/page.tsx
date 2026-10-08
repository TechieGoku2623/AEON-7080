"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function ExperimentsPage() {
  const token = useToken();
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    if (!token) return;
    api<{ experiments: any[] }>("/api/experiments", token).then((payload) => setRows(payload.experiments));
  }, [token]);
  return (
    <div className="space-y-4">
      <Label>Reproducible runs</Label>
      <h1 className="font-serif text-4xl">My experiments</h1>
      {rows.map((row) => (
        <Link key={row.id} href={`/experiments/${row.id}`}>
          <Panel className="flex items-center justify-between">
            <div>
              <h2 className="font-serif text-2xl">{row.title}</h2>
              <p className="font-mono text-xs text-mute">seed {row.seed} · {row.status}</p>
            </div>
            <span className="font-mono text-xs text-cyan">{row.id.slice(0, 8)}</span>
          </Panel>
        </Link>
      ))}
      {rows.length === 0 && <p className="text-mute">No experiments yet. Run one from the PK/PD lab.</p>}
    </div>
  );
}
