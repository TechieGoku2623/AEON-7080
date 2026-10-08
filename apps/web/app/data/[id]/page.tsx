"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api, ApiError } from "@/lib/api";

export default function DatasetPage() {
  const token = useToken();
  const params = useParams<{ id: string }>();
  const [record, setRecord] = useState<any>(null);
  const [question, setQuestion] = useState("What is associated with glucose?");
  const [answer, setAnswer] = useState<any>(null);
  const [mappingResult, setMappingResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api(`/api/data/${params.id}`, token).then(setRecord).catch((err) => setError(err.message));
  }, [token, params.id]);

  async function ask() {
    if (!token) return;
    setAnswer(await api(`/api/data/${params.id}/analyze`, token, { method: "POST", body: JSON.stringify({ question }) }));
  }

  async function confirmMap() {
    if (!token || !record) return;
    setError("");
    try {
      const mapping = (record.suggestions || []).map((item: any) => ({ ...item, confirmed: true }));
      const result = await api(`/api/data/${params.id}/map`, token, {
        method: "POST",
        body: JSON.stringify({ mapping, confirmed: true, row_index: 0 }),
      });
      setMappingResult(result);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        await api(`/api/data/${params.id}/acknowledge`, token, { method: "POST" });
        setError(`${err.message} Acknowledgement was recorded. Confirm the mapping again if you are authorized to use it.`);
        return;
      }
      setError(err instanceof Error ? err.message : "Mapping failed");
    }
  }

  if (!record) return <p>{error || "Loading the dataset…"}</p>;
  const profile = record.profile || {};
  return (
    <div className="space-y-4">
      <Label>{record.permission?.allow_training ? "Training allowed" : "Training off"}</Label>
      <h1 className="font-serif text-4xl">{record.name}</h1>
      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Rows" value={profile.rows} />
        <Stat label="Columns" value={profile.columns} />
        <Stat label="Numerical" value={profile.numerical?.length} />
        <Stat label="Missing" value={profile.missing_fraction != null ? `${(profile.missing_fraction * 100).toFixed(1)}%` : "—"} />
      </div>
      <Panel>
        <Label>Quality heuristic · {record.quality?.score}</Label>
        <p className="mt-2 text-sm text-mute">{record.quality?.label}</p>
        <ul className="mt-2 text-sm">{(record.quality?.deductions || []).map((item: string) => <li key={item}>{item}</li>)}</ul>
      </Panel>
      {profile.sensitive?.potentially_sensitive && (
        <Panel>
          <Label>Potentially sensitive data</Label>
          <p className="mt-2 text-sm text-amber">{profile.sensitive.warning}</p>
          <p className="mt-2 text-xs text-mute">{profile.sensitive.guarantee}</p>
        </Panel>
      )}
      <Panel>
        <Label>Preview</Label>
        <div className="mt-3 overflow-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr>{(profile.column_names || []).map((column: string) => <th key={column} className="border-b border-line px-2 py-1 font-mono text-xs">{column}</th>)}</tr>
            </thead>
            <tbody>
              {(profile.preview || []).slice(0, 8).map((row: any, index: number) => (
                <tr key={index}>{(profile.column_names || []).map((column: string) => <td key={column} className="px-2 py-1 font-mono text-xs">{String(row[column])}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <Panel>
        <Label>Ask this table</Label>
        <div className="mt-3 flex gap-2">
          <input className="flex-1 rounded border border-line bg-ink px-2 py-1" value={question} onChange={(e) => setQuestion(e.target.value)} />
          <Button type="button" onClick={ask}>Ask</Button>
        </div>
        {answer && <pre className="mt-3 overflow-auto font-mono text-xs">{JSON.stringify(answer, null, 2)}</pre>}
      </Panel>
      <Panel>
        <Label>Map data to model</Label>
        <p className="mt-2 text-sm text-mute">Suggestions do nothing until you confirm them.</p>
        <ul className="mt-2 font-mono text-xs">
          {(record.suggestions || []).map((item: any) => <li key={item.parameter}>{item.column} → {item.parameter}</li>)}
        </ul>
        <Button className="mt-3" type="button" variant="ghost" onClick={confirmMap}>Confirm mapping for row 1</Button>
        {mappingResult && <p className="mt-2 text-sm text-cyan">{mappingResult.label}: {JSON.stringify(mappingResult.parameters)}</p>}
        {error && <p className="mt-2 text-sm text-amber">{error}</p>}
      </Panel>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <Panel><p className="font-mono text-[10px] uppercase text-mute">{label}</p><p className="font-serif text-3xl">{value ?? "—"}</p></Panel>;
}
