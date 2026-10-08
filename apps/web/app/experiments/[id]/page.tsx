"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Workbench, type ExperimentPayload } from "@/components/simulation/workbench";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function ExperimentPage() {
  const token = useToken();
  const params = useParams<{ id: string }>();
  const [record, setRecord] = useState<any>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!token) return;
    api(`/api/experiments/${params.id}`, token).then(setRecord);
  }, [token, params.id]);

  async function replay() {
    if (!token) return;
    const response = await api<{ matched_previous: boolean; result: ExperimentPayload }>(`/api/experiments/${params.id}/replay`, token, { method: "POST" });
    setNotice(response.matched_previous ? "Replay matched the stored endpoint values." : "Replay did not match. Inspect the seed and configuration.");
    setRecord((current: any) => ({ ...current, result: response.result }));
  }

  if (!record) return <p>Loading the experiment…</p>;
  return (
    <div className="space-y-4">
      <Label>Experiment {record.id}</Label>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-serif text-4xl">{record.title}</h1>
        <Button type="button" variant="ghost" onClick={replay}>Replay</Button>
      </div>
      {notice && <p className="text-cyan">{notice}</p>}
      {record.result ? <Workbench payload={record.result} /> : <p>This experiment has not been run.</p>}
    </div>
  );
}
