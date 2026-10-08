"use client";

import { useEffect, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

export default function ComparePage() {
  const token = useToken();
  const [rows, setRows] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<any>(null);

  useEffect(() => {
    if (!token) return;
    api<{ experiments: any[] }>("/api/experiments", token).then((payload) => setRows(payload.experiments));
  }, [token]);

  function toggle(id: string) {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id].slice(-3));
  }

  async function compare() {
    if (!token) return;
    setComparison(await api(`/api/experiments/compare?ids=${selected.join(",")}`, token));
  }

  return (
    <div className="space-y-4">
      <Label>Comparison</Label>
      <h1 className="font-serif text-4xl">Compare experiments</h1>
      <div className="grid gap-2">
        {rows.map((row) => (
          <label key={row.id} className="flex items-center gap-2 rounded border border-line px-3 py-2 text-sm">
            <input type="checkbox" checked={selected.includes(row.id)} onChange={() => toggle(row.id)} />
            {row.title} · {row.id.slice(0, 8)}
          </label>
        ))}
      </div>
      <Button type="button" onClick={compare} disabled={selected.length < 2}>Compare</Button>
      {comparison && (
        <div className="grid gap-3 md:grid-cols-2">
          {comparison.comparison.map((item: any) => (
            <Panel key={item.id}>
              <h2 className="font-serif text-2xl">{item.title}</h2>
              <p className="font-mono text-xs text-mute">seed {item.seed}</p>
              {Object.entries(item.drugs).map(([name, drug]: any) => (
                <p key={name} className="mt-2 text-sm">{name}: nadir Δ glucose {formatNumber(drug.endpoints?.glucose_nadir_delta_mg_dl, 2)} mg/dL</p>
              ))}
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}
