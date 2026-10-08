"use client";

import { useState } from "react";
import { ModelLab } from "@/components/simulation/model-lab";

const TABS = {
  heart: {
    model: "cardiovascular",
    title: "Cardiovascular bookkeeping",
    description: "Heart rate relaxes toward a command. Output is cardiac output and a mean pressure from fixed resistance. There is no baroreflex.",
    seriesKey: "heart_rate_bpm",
    defaults: { heart_rate_bpm: 72, stroke_volume_ml: 70, systolic_mmhg: 120, diastolic_mmhg: 80, hr_command_bpm: 90, tau_h: 0.05, cvp_mmhg: 5 },
  },
  glucose: {
    model: "glucose_insulin",
    title: "Glucose–insulin bookkeeping",
    description: "Glucose returns to the supplied baseline. The insulin trace is an illustrative scale, not a clinical assay.",
    seriesKey: "glucose_mg_dl",
    defaults: { glucose_mg_dl: 140, insulin_mu_l: 8, k_glucose_per_h: 0.4, k_insulin_per_h: 0.35, insulin_slope: 0.04 },
  },
  breath: {
    model: "respiratory",
    title: "Respiratory bookkeeping",
    description: "Minute ventilation is rate times tidal volume. The saturation index is not SpO2.",
    seriesKey: "minute_ventilation_l_min",
    defaults: { respiratory_rate_per_min: 14, tidal_volume_l: 0.5, dead_space_l: 0.15, reference_alveolar_l_min: 5 },
  },
} as const;

export default function PhysiologyPage() {
  const [tab, setTab] = useState<keyof typeof TABS>("heart");
  const current = TABS[tab];
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {(Object.keys(TABS) as (keyof typeof TABS)[]).map((key) => (
          <button key={key} className={`rounded-md border px-3 py-1 text-sm ${tab === key ? "border-cyan text-cyan" : "border-line"}`} onClick={() => setTab(key)}>
            {key}
          </button>
        ))}
      </div>
      <ModelLab key={current.model} {...current} />
    </div>
  );
}
