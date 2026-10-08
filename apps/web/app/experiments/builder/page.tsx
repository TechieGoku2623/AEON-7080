"use client";

import { useCallback, useState } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRouter } from "next/navigation";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/panel";
import { api } from "@/lib/api";

const initialNodes: Node[] = [
  ["dataset", "Synthetic patient", 0],
  ["map", "Parameters", 1],
  ["pk", "Oral PK", 2],
  ["pd", "Glucose PD", 3],
  ["mc", "Monte Carlo", 4],
  ["critic", "Critic", 5],
  ["report", "Report", 6],
].map(([id, label, index]) => ({
  id: String(id),
  position: { x: 40 + Number(index) * 40, y: 40 + Number(index) * 70 },
  data: { label: String(label) },
  style: { background: "#10202b", color: "#e6eef2", border: "1px solid #234554", width: 180 },
}));

const initialEdges: Edge[] = [
  ["dataset", "map"],
  ["map", "pk"],
  ["pk", "pd"],
  ["pd", "mc"],
  ["mc", "critic"],
  ["critic", "report"],
].map(([source, target], index) => ({ id: `e${index}`, source, target }));

export default function BuilderPage() {
  const token = useToken();
  const router = useRouter();
  const [nodes, setNodes] = useState(initialNodes);
  const [busy, setBusy] = useState(false);

  const run = useCallback(async () => {
    if (!token) return;
    setBusy(true);
    const created = await api<{ id: string }>("/api/experiments", token, {
      method: "POST",
      body: JSON.stringify({ title: "Builder graph", template_id: "drug-response", config: { mode: "patient", monte_carlo: { n: 80, cv: 0.15 }, duration_h: 12, dt_h: 0.1 } }),
    });
    await api(`/api/experiments/${created.id}/run`, token, { method: "POST" });
    setNodes((current) => current.map((node) => ({ ...node, data: { ...node.data, label: `${String(node.data.label)} · done` } })));
    setBusy(false);
    router.push(`/experiments/${created.id}`);
  }, [router, token]);

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <Label>React Flow</Label>
          <h1 className="font-serif text-4xl">Experiment builder</h1>
        </div>
        <Button type="button" onClick={run} disabled={busy}>{busy ? "Running graph" : "Run graph"}</Button>
      </div>
      <div className="h-[520px] overflow-hidden rounded-xl border border-line">
        <ReactFlow nodes={nodes} edges={initialEdges} fitView colorMode="dark">
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}
