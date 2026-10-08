"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

const DigitalHuman = dynamic(() => import("@/components/simulation/digital-human").then((m) => m.DigitalHuman), { ssr: false });

export default function DigitalTwinPage() {
  const token = useToken();
  const [state, setState] = useState<{ glucose: number; heart: number; note: string } | null>(null);

  async function condition() {
    if (!token) return;
    const patient = await api<any>("/api/patients/generate", token, {
      method: "POST",
      body: JSON.stringify({ seed: 11, condition: "synthetic_diabetes" }),
    });
    const cardio = await api<any>("/api/simulations/run", token, {
      method: "POST",
      body: JSON.stringify({
        model: "cardiovascular",
        parameters: {
          heart_rate_bpm: patient.heart_rate_bpm,
          stroke_volume_ml: patient.stroke_volume_ml,
          systolic_mmhg: patient.blood_pressure_mmhg.systolic,
          diastolic_mmhg: patient.blood_pressure_mmhg.diastolic,
          hr_command_bpm: patient.heart_rate_bpm + 8,
          tau_h: 0.05,
          cvp_mmhg: 5,
        },
        duration: 2,
        dt: 0.05,
        seed: 11,
      }),
    });
    const hr = cardio.results.heart_rate_bpm.at(-1);
    setState({
      glucose: patient.glucose_mg_dl,
      heart: hr,
      note: "DATA-CONDITIONED COMPUTATIONAL MODEL is reserved for a confirmed upload. This view is conditioned on a synthetic record.",
    });
  }

  return (
    <div className="space-y-4">
      <Label>Schematic twin</Label>
      <h1 className="font-serif text-4xl">Digital twin</h1>
      <Button type="button" onClick={condition}>Condition on a synthetic record</Button>
      {state && (
        <>
          <DigitalHuman glucose={state.glucose} heartRate={state.heart} />
          <Panel><p className="text-sm text-mute">{state.note}</p></Panel>
        </>
      )}
    </div>
  );
}
