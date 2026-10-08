"use client";

import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function MLPage() {
  const token = useToken();
  const [result, setResult] = useState<any>(null);

  async function train() {
    if (!token) return;
    setResult(await api("/api/ml/train", token, { method: "POST", body: JSON.stringify({ seed: 5 }) }));
  }

  const loss = (result?.loss_curve || []).map((value: number, epoch: number) => ({ epoch, loss: value }));
  return (
    <div className="space-y-4">
      <Label>Numpy logistic regression</Label>
      <h1 className="font-serif text-4xl">AI/ML lab</h1>
      <p className="max-w-3xl text-mute">Trains on synthetic T-wave classes only. PyTorch runs when installed. TensorFlow is reported as unavailable rather than simulated.</p>
      <Button type="button" onClick={train}>Train on synthetic data</Button>
      {result && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel>
            <p>MODEL PREDICTION · held-out accuracy {result.metrics.accuracy.toFixed(3)}</p>
            <p className="mt-2 font-mono text-xs">Confusion {JSON.stringify(result.metrics.confusion_matrix)}</p>
            <p className="mt-2 text-xs text-mute">{result.architecture.type} · {result.architecture.implementation}</p>
            <pre className="mt-3 font-mono text-xs">{JSON.stringify(result.frameworks, null, 2)}</pre>
          </Panel>
          <Panel>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={loss}>
                  <CartesianGrid stroke="#234554" />
                  <XAxis dataKey="epoch" stroke="#8ea4ae" />
                  <YAxis stroke="#8ea4ae" />
                  <Tooltip contentStyle={{ background: "#10202b", border: "1px solid #234554" }} />
                  <Line dataKey="loss" stroke="#7ee0d0" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}
