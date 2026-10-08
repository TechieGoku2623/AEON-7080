"use client";

import { useState } from "react";
import { Workbench, type ExperimentPayload } from "@/components/simulation/workbench";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

const EXAMPLE = "Compare two hypothetical treatments in a virtual diabetic population.";

export default function ScientistPage() {
  const token = useToken();
  const [question, setQuestion] = useState(EXAMPLE);
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<ExperimentPayload | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  async function planOnly() {
    if (!token) return;
    setBusy(true);
    setNote("");
    try {
      const response = await api<{ plan: Record<string, unknown> }>("/api/ai/plan", token, {
        method: "POST",
        body: JSON.stringify({ message: question }),
      });
      setPlan(response.plan);
      setResult(null);
    } catch (err) {
      setNote(err instanceof Error ? err.message : "Plan failed");
    } finally {
      setBusy(false);
    }
  }

  async function execute() {
    if (!token) return;
    setBusy(true);
    setNote("");
    try {
      const response = await api<{ plan: Record<string, unknown>; executed: boolean; result: ExperimentPayload | null }>(
        "/api/ai/execute",
        token,
        { method: "POST", body: JSON.stringify({ message: question, execute: true }) },
      );
      setPlan(response.plan);
      setResult(response.result);
      if (!response.executed) setNote(String((response.plan as { reason?: string }).reason || "Not executed."));
    } catch (err) {
      setNote(err instanceof Error ? err.message : "Execute failed");
    } finally {
      setBusy(false);
    }
  }

  const tools = (plan?.tools as string[]) || [];
  return (
    <div className="space-y-4">
      <Label>AI Scientist</Label>
      <h1 className="font-serif text-4xl">What would you like to investigate?</h1>
      <Panel>
        <textarea
          className="min-h-28 w-full rounded-md border border-line bg-ink p-3"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Button type="button" variant="ghost" onClick={planOnly} disabled={busy}>Show plan</Button>
          <Button type="button" onClick={execute} disabled={busy}>{busy ? "Running tools" : "Run experiment"}</Button>
        </div>
        {note && <p className="mt-3 text-sm text-amber">{note}</p>}
      </Panel>
      {plan && (
        <Panel>
          <Label>Experiment plan</Label>
          <ul className="mt-3 space-y-1 text-sm">
            {tools.map((tool) => (
              <li key={tool} className="font-mono text-cyan">✓ {tool}</li>
            ))}
            {tools.length === 0 && <li>No tools. {(plan as { reason?: string }).reason}</li>}
          </ul>
          <pre className="mt-3 overflow-auto rounded bg-ink p-3 font-mono text-xs">{JSON.stringify(plan, null, 2)}</pre>
        </Panel>
      )}
      {result?.drugs && <Workbench payload={result} />}
      {result && !result.drugs && (
        <Panel>
          <p>{result.explanation}</p>
        </Panel>
      )}
    </div>
  );
}
