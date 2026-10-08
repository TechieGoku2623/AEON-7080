"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

const DigitalHuman = dynamic(() => import("@/components/simulation/digital-human").then((m) => m.DigitalHuman), { ssr: false });

export default function VirtualPatientPage() {
  const token = useToken();
  const [seed, setSeed] = useState(42);
  const [patient, setPatient] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState("");

  async function generate() {
    if (!token) return;
    setError("");
    try {
      const record = await api<Record<string, any>>("/api/patients/generate", token, {
        method: "POST",
        body: JSON.stringify({ seed, condition: "synthetic_diabetes" }),
      });
      setPatient(record);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate");
    }
  }

  return (
    <div className="space-y-4">
      <Label>Synthetic data</Label>
      <h1 className="font-serif text-4xl">Virtual patient</h1>
      <Panel className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Seed
          <input className="mt-1 block rounded border border-line bg-ink px-2 py-1" type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
        </label>
        <Button type="button" onClick={generate}>Generate</Button>
        {patient && <Link className="text-sm text-cyan" href={`/labs/pharmacology?seed=${patient.seed}`}>Use in the PK/PD lab</Link>}
      </Panel>
      {error && <p className="text-amber">{error}</p>}
      {patient && (
        <div className="grid gap-4 lg:grid-cols-2">
          <DigitalHuman glucose={patient.glucose_mg_dl} heartRate={patient.heart_rate_bpm} />
          <Panel>
            <p className="font-mono text-xs text-amber">{patient.label}</p>
            <dl className="mt-3 grid grid-cols-2 gap-2 font-mono text-sm">
              <div>Age {patient.age}</div>
              <div>BMI {patient.bmi}</div>
              <div>{patient.height_cm} cm</div>
              <div>{patient.weight_kg} kg</div>
              <div>Glucose {patient.glucose_mg_dl} mg/dL</div>
              <div>HR {patient.heart_rate_bpm} bpm</div>
              <div>SBP {patient.blood_pressure_mmhg.systolic}</div>
              <div>DBP {patient.blood_pressure_mmhg.diastolic}</div>
            </dl>
            <p className="mt-3 text-xs text-mute">{patient.note}</p>
          </Panel>
        </div>
      )}
    </div>
  );
}
