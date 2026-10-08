"use client";

import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";
import { decimate } from "@/lib/series";

export default function BiosignalsPage() {
  const token = useToken();
  const [rows, setRows] = useState<{ time: number; value: number }[]>([]);
  const [features, setFeatures] = useState<Record<string, number> | null>(null);
  const [prediction, setPrediction] = useState<string>("");
  const [error, setError] = useState("");

  async function generate() {
    if (!token) return;
    setError("");
    try {
      const result = await api<{ results: { time: number[]; amplitude: number[]; features: Record<string, number> } }>(
        "/api/simulations/run",
        token,
        { method: "POST", body: JSON.stringify({ model: "synthetic_ecg", parameters: { heart_rate_bpm: 72, duration_s: 8, fs_hz: 250, noise_std: 0.02, t_wave_scale: 1 }, duration: 8, dt: 0.004, seed: 4 }) },
      );
      const workerRows = await decimateInWorker(result.results.amplitude);
      const time = result.results.time;
      setRows(workerRows.map((point) => ({ time: time[point.i], value: point.v })));
      setFeatures(result.results.features);
      const ml = await api<{ prediction: { class: string; probability_class_b: number }; metrics: { accuracy: number } }>(
        "/api/ml/predict",
        token,
        { method: "POST", body: JSON.stringify({ t_wave_mean: result.results.features.t_wave_mean, seed: 4 }) },
      );
      setPrediction(`MODEL PREDICTION ${ml.prediction.class} (p=${ml.prediction.probability_class_b.toFixed(2)}), synthetic test accuracy ${ml.metrics.accuracy.toFixed(2)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ECG failed");
    }
  }

  return (
    <div className="space-y-4">
      <Label>Synthetic ECG</Label>
      <h1 className="font-serif text-4xl">Biosignal lab</h1>
      <p className="max-w-3xl text-mute">Gaussian-wave waveform, a bandpass is available on the server for uploaded workflows, and the classifier only separates synthetic T-wave classes.</p>
      <Button type="button" onClick={generate}>Generate ECG</Button>
      {error && <p className="text-amber">{error}</p>}
      <Panel>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows}>
              <CartesianGrid stroke="#234554" />
              <XAxis dataKey="time" stroke="#8ea4ae" />
              <YAxis stroke="#8ea4ae" />
              <Tooltip contentStyle={{ background: "#10202b", border: "1px solid #234554" }} />
              <Line dataKey="value" stroke="#e7c27a" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
      {features && (
        <Panel>
          <pre className="font-mono text-xs">{JSON.stringify(features, null, 2)}</pre>
          <p className="mt-2 text-sm">{prediction}</p>
        </Panel>
      )}
    </div>
  );
}

function decimateInWorker(values: number[]): Promise<{ i: number; v: number }[]> {
  return new Promise((resolve) => {
    try {
      const worker = new Worker(new URL("../../../workers/decimate.ts", import.meta.url));
      worker.onmessage = (event) => {
        resolve(event.data);
        worker.terminate();
      };
      worker.postMessage({ values, maxPoints: 800 });
    } catch {
      resolve(decimate(values, 800));
    }
  });
}
