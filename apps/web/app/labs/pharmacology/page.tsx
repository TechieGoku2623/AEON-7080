"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Workbench, type ExperimentPayload } from "@/components/simulation/workbench";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

function PharmacologyLab() {
  const token = useToken();
  const params = useSearchParams();
  const seed = Number(params.get("seed") || 42);
  const [payload, setPayload] = useState<ExperimentPayload | null>(null);
  const [experimentId, setExperimentId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      const created = await api<{ id: string }>("/api/experiments", token, {
        method: "POST",
        body: JSON.stringify({
          title: "Drug response in a virtual patient",
          template_id: "drug-response",
          config: { seed, mode: "patient", monte_carlo: { n: 200, cv: 0.2 }, duration_h: 24, dt_h: 0.1 },
        }),
      });
      const ran = await api<{ experiment_id: string; result: ExperimentPayload }>(`/api/experiments/${created.id}/run`, token, { method: "POST" });
      setExperimentId(ran.experiment_id);
      setPayload(ran.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Label>PK/PD lab</Label>
          <h1 className="font-serif text-4xl">Drug response in a virtual patient</h1>
          <p className="mt-2 max-w-3xl text-mute">
            Treatment A and Treatment B are hypothetical parameter sets. The curves come from an oral one-compartment model and an indirect glucose response.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/academy" className="rounded-md border border-line px-3 py-2 text-sm">Watch demo</Link>
          <Button type="button" onClick={run} disabled={busy}>{busy ? "Computing" : "Run simulation"}</Button>
        </div>
      </div>
      <Panel>
        <p className="font-mono text-xs text-mute">Seed {seed}. Monte Carlo n = 200. Validated for software correctness, not clinical use.</p>
        {experimentId && <p className="mt-2 text-sm">Experiment {experimentId}. <Link className="text-cyan" href={`/experiments/${experimentId}`}>Open the record</Link></p>}
        {error && <p className="mt-2 text-amber">{error}</p>}
      </Panel>
      {payload && <Workbench payload={payload} />}
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<p>Loading the lab…</p>}>
      <PharmacologyLab />
    </Suspense>
  );
}
