"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";

export default function UploadPage() {
  const token = useToken();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [experiments, setExperiments] = useState(true);
  const [training, setTraining] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!token || !file) return;
    const body = new FormData();
    body.set("file", file);
    body.set("name", file.name);
    body.set("use_in_experiments", String(experiments));
    body.set("allow_training", String(training));
    body.set("allow_analytics", String(analytics));
    const response = await fetch("/api/data/upload", { method: "POST", headers: { Authorization: `Bearer ${token}` }, body });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.detail || "Upload failed");
      return;
    }
    router.push(`/data/${payload.id}`);
  }

  return (
    <div className="space-y-4">
      <Label>Import</Label>
      <h1 className="font-serif text-4xl">Upload a table</h1>
      <Panel
        className="grid min-h-48 place-items-center border-dashed text-center"
      >
        <div>
          <p className="font-serif text-2xl">Drop your data here</p>
          <p className="my-3 text-mute">or</p>
          <input aria-label="Select files" type="file" accept=".csv,.tsv,.json" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <p className="mt-3 font-mono text-xs text-mute">CSV · TSV · JSON</p>
        </div>
      </Panel>
      <Panel>
        <Label>Data usage</Label>
        <label className="mt-3 flex gap-2 text-sm"><input type="checkbox" checked={experiments} onChange={(e) => setExperiments(e.target.checked)} /> Use this dataset in my experiments</label>
        <label className="mt-2 flex gap-2 text-sm"><input type="checkbox" checked={training} onChange={(e) => setTraining(e.target.checked)} /> Allow this dataset to be used for model training</label>
        <label className="mt-2 flex gap-2 text-sm"><input type="checkbox" checked={analytics} onChange={(e) => setAnalytics(e.target.checked)} /> Allow anonymized metadata for platform analytics</label>
        <p className="mt-2 text-xs text-mute">Training and analytics stay off unless you check them. Upload does not train a model.</p>
        <Button className="mt-4" type="button" onClick={submit} disabled={!file}>Continue</Button>
        {error && <p className="mt-2 text-amber">{error}</p>}
      </Panel>
    </div>
  );
}
