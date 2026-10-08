"use client";

import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";
import { useToken } from "@/components/shell/session";

export function ModelLab({
  model,
  title,
  description,
  defaults,
  seriesKey,
}: {
  model: string;
  title: string;
  description: string;
  defaults: Record<string, number>;
  seriesKey: string;
}) {
  const token = useToken();
  const [params, setParams] = useState(defaults);
  const [rows, setRows] = useState<{ time: number; value: number }[]>([]);
  const [meta, setMeta] = useState<string>("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run() {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<{
        results: Record<string, number[] | number>;
        validation: string;
        solver: string;
        labels: string[];
      }>("/api/simulations/run", token, {
        method: "POST",
        body: JSON.stringify({ model, parameters: params, duration: model === "sir" || model === "seir" ? 60 : 24, dt: 0.1, seed: 42 }),
      });
      const time = result.results.time as number[];
      const values = result.results[seriesKey] as number[];
      setRows(time.map((t, i) => ({ time: t, value: values[i] })));
      setMeta(`${result.validation} · ${result.solver}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <Label>Simplified computational model</Label>
        <h1 className="mt-1 font-serif text-4xl">{title}</h1>
        <p className="mt-2 max-w-3xl text-mute">{description}</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <Panel>
          <div className="space-y-3">
            {Object.entries(params).map(([key, value]) => (
              <label key={key} className="block text-sm">
                <span className="font-mono text-xs text-mute">{key}</span>
                <input
                  className="mt-1 w-full rounded border border-line bg-ink px-2 py-1"
                  type="number"
                  value={value}
                  step="any"
                  onChange={(e) => setParams({ ...params, [key]: Number(e.target.value) })}
                />
              </label>
            ))}
            <Button type="button" onClick={run} disabled={busy}>{busy ? "Running" : "Run simulation"}</Button>
            {error && <p className="text-sm text-amber">{error}</p>}
          </div>
        </Panel>
        <Panel>
          <p className="mb-2 font-mono text-xs text-mute">{meta || seriesKey}</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rows}>
                <CartesianGrid stroke="#234554" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#8ea4ae" />
                <YAxis stroke="#8ea4ae" />
                <Tooltip contentStyle={{ background: "#10202b", border: "1px solid #234554" }} />
                <Line dataKey="value" stroke="#7ee0d0" dot={false} name={seriesKey} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
}
