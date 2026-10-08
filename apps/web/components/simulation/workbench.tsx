"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Equation } from "@/components/simulation/equation";
import { Label, Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/lib/utils";

const DigitalHuman = dynamic(() => import("@/components/simulation/digital-human").then((m) => m.DigitalHuman), {
  ssr: false,
});

type Drug = {
  series?: {
    time_h: number[];
    concentration_mg_l: number[];
    glucose_mg_dl: number[];
    insulin_mu_l: number[];
    heart_rate_bpm: number[];
  };
  endpoints?: Record<string, number | null>;
  monte_carlo?: {
    n: number;
    glucose_p05: number[];
    glucose_p95: number[];
    endpoint_summary?: { mean: number; p05: number; p50: number; p95: number };
    interpretation?: string;
  };
  sensitivity?: { bars?: { parameter: string; low_output: number; high_output: number; swing: number }[]; most_influential?: string };
  parameters?: Record<string, number>;
  glucose_state_12h?: string;
  glucose_state_note?: string;
};

export type ExperimentPayload = {
  labels?: string[];
  patient?: Record<string, unknown> | null;
  explanation?: string;
  hypothesis?: { observation?: string; hypothesis?: string; suggested_experiment?: string; influential_parameters?: string[] };
  critic?: { status?: string; flags?: string[]; changed_parameters?: boolean };
  drugs?: Record<string, Drug>;
  ecg?: { baseline?: { time_s: number[]; amplitude: number[] }; baseline_features?: Record<string, number> };
  ml?: { metrics?: { accuracy?: number; confusion_matrix?: number[][] }; prediction?: { class?: string; probability_class_b?: number }; architecture?: { type?: string } };
  equations?: { latex: string; description: string }[];
  assumptions?: string[];
  limitations?: string[];
  reproducibility?: { seed?: number; config_fingerprint?: string; software_version?: string; model_versions?: Record<string, string> };
  report_markdown?: string;
  stages?: { id: string; status: string; summary: string }[];
};

export function Workbench({ payload }: { payload: ExperimentPayload }) {
  const drugs = payload.drugs || {};
  const names = Object.keys(drugs);
  const primary = drugs[names[0]];
  const time = primary?.series?.time_h || [];
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [showReport, setShowReport] = useState(false);
  const [showHood, setShowHood] = useState(false);

  useEffect(() => setIndex(0), [payload]);
  useEffect(() => {
    if (!playing || time.length < 2) return;
    const timer = window.setInterval(() => {
      setIndex((current) => {
        if (current >= time.length - 1) {
          setPlaying(false);
          return current;
        }
        return Math.min(time.length - 1, current + speed);
      });
    }, 80);
    return () => window.clearInterval(timer);
  }, [playing, speed, time.length]);

  const rows = useMemo(() => {
    return time.map((hour, i) => {
      const row: Record<string, number> = { time: hour };
      names.forEach((name) => {
        const drug = drugs[name];
        row[`${name}_c`] = drug.series?.concentration_mg_l[i] ?? 0;
        row[`${name}_g`] = drug.series?.glucose_mg_dl[i] ?? 0;
        row[`${name}_i`] = drug.series?.insulin_mu_l[i] ?? 0;
        if (drug.monte_carlo && drug.monte_carlo.glucose_p05.length === time.length) {
          row[`${name}_lo`] = drug.monte_carlo.glucose_p05[i];
          row[`${name}_hi`] = drug.monte_carlo.glucose_p95[i];
        }
      });
      return row;
    });
  }, [drugs, names, time]);

  const sample = rows[Math.min(index, Math.max(rows.length - 1, 0))] || {};
  const glucose = Number(sample[`${names[0]}_g`] ?? payload.patient?.glucose_mg_dl ?? 100);
  const heart = Number(primary?.series?.heart_rate_bpm[index] ?? payload.patient?.heart_rate_bpm ?? 72);
  const concentration = Number(sample[`${names[0]}_c`] ?? 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {(payload.labels || []).map((label) => (
          <span key={label} className="rounded-full border border-amber/40 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-amber">
            {label}
          </span>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <Panel>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Button type="button" onClick={() => setPlaying((v) => !v)}>{playing ? "Pause" : "Play"}</Button>
            <Button type="button" variant="ghost" onClick={() => setIndex((v) => Math.min(time.length - 1, v + 1))}>Step</Button>
            <Button type="button" variant="ghost" onClick={() => { setPlaying(false); setIndex(0); }}>Reset</Button>
            <label className="font-mono text-xs text-mute">
              Speed
              <select className="ml-2 rounded border border-line bg-ink px-2 py-1" value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
                <option value={1}>1×</option>
                <option value={2}>2×</option>
                <option value={4}>4×</option>
              </select>
            </label>
            <span className="font-mono text-xs text-cyan">{formatNumber(time[index] || 0, 2)} h</span>
          </div>
          <input
            aria-label="Timeline"
            className="w-full accent-cyan"
            type="range"
            min={0}
            max={Math.max(time.length - 1, 0)}
            value={Math.min(index, Math.max(time.length - 1, 0))}
            onChange={(e) => setIndex(Number(e.target.value))}
          />
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rows}>
                <CartesianGrid stroke="#234554" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#8ea4ae" tick={{ fontSize: 11 }} />
                <YAxis stroke="#8ea4ae" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#10202b", border: "1px solid #234554" }} />
                {names.map((name, i) => (
                  <Line key={name} type="monotone" dataKey={`${name}_g`} name={`${name} glucose`} stroke={i === 0 ? "#7ee0d0" : "#e7c27a"} dot={false} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-mute">Simulated glucose, mg/dL</p>
        </Panel>
        <div className="space-y-3">
          <DigitalHuman glucose={glucose} heartRate={heart} concentration={concentration} />
          <div className="grid grid-cols-3 gap-2 text-center">
            <Stat label="Glucose" value={`${formatNumber(glucose, 1)} mg/dL`} />
            <Stat label="Heart rate" value={`${formatNumber(heart, 1)} bpm`} />
            <Stat label="Concentration" value={`${formatNumber(concentration, 2)} mg/L`} />
          </div>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {names.map((name) => (
          <Panel key={name}>
            <Label>{name}</Label>
            <h3 className="mt-1 font-serif text-xl">Hypothetical parameter set</h3>
            <dl className="mt-3 grid grid-cols-2 gap-2 font-mono text-sm">
              <Metric term="Nadir Δ glucose" value={drugs[name].endpoints?.glucose_nadir_delta_mg_dl} unit="mg/dL" />
              <Metric term="Δ glucose 12 h" value={drugs[name].endpoints?.glucose_delta_12h_mg_dl} unit="mg/dL" />
              <Metric term="Cmax" value={drugs[name].endpoints?.cmax_mg_l} unit="mg/L" />
              <Metric term="Uncertainty mean" value={drugs[name].monte_carlo?.endpoint_summary?.mean} unit="mg/dL" />
              <Metric term="p05 – p95" value={undefined} text={span(drugs[name])} />
            </dl>
            <p className="mt-3 text-xs text-mute">{drugs[name].monte_carlo?.interpretation}</p>
            <p className="mt-2 text-xs text-amber">{drugs[name].glucose_state_note} {drugs[name].glucose_state_12h}</p>
          </Panel>
        ))}
      </div>
      <Panel>
        <Label>Sensitivity</Label>
        <div className="mt-3 space-y-2">
          {(primary?.sensitivity?.bars || []).map((bar) => (
            <div key={bar.parameter} className="grid grid-cols-[90px_1fr_80px] items-center gap-2 text-sm">
              <span className="font-mono text-xs">{bar.parameter}</span>
              <div className="h-2 rounded bg-ink">
                <div className="h-2 rounded bg-cyan" style={{ width: `${Math.min(100, (bar.swing / swingMax(primary)) * 100)}%` }} />
              </div>
              <span className="font-mono text-xs text-mute">{formatNumber(bar.swing, 2)}</span>
            </div>
          ))}
          {!primary?.sensitivity?.bars?.length && <p className="text-sm text-mute">One-at-a-time sensitivity is included in patient mode.</p>}
        </div>
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <Label>AI Scientist</Label>
          <p className="mt-2 text-sm leading-6">{payload.explanation}</p>
          {payload.hypothesis && (
            <div className="mt-4 border-t border-line pt-3 text-sm">
              <p>{payload.hypothesis.observation}</p>
              <p className="mt-2 text-mute">{payload.hypothesis.hypothesis}</p>
              <p className="mt-2 font-mono text-xs text-cyan">{payload.hypothesis.suggested_experiment}</p>
            </div>
          )}
        </Panel>
        <Panel>
          <Label>Scientific critic · {payload.critic?.status || "n/a"}</Label>
          <ul className="mt-2 space-y-1 text-sm">
            {(payload.critic?.flags || []).length === 0 && <li>No flags. Parameters were not rewritten.</li>}
            {(payload.critic?.flags || []).map((flag) => (
              <li key={flag} className="text-amber">{flag}</li>
            ))}
          </ul>
          {payload.ml?.metrics && (
            <p className="mt-4 font-mono text-xs text-mute">
              MODEL PREDICTION · synthetic morphology accuracy {formatNumber(payload.ml.metrics.accuracy, 2)} · class {payload.ml.prediction?.class || "n/a"}
            </p>
          )}
        </Panel>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="ghost" onClick={() => setShowHood((v) => !v)}>Under the hood</Button>
        <Button type="button" variant="ghost" onClick={() => setShowReport((v) => !v)}>Report</Button>
      </div>
      {showHood && (
        <Panel>
          <Label>Under the hood</Label>
          <div className="mt-3 space-y-3">
            {(payload.equations || []).map((equation) => (
              <div key={equation.latex}>
                <Equation latex={equation.latex} />
                <p className="text-xs text-mute">{equation.description}</p>
              </div>
            ))}
            <p className="font-mono text-xs">Seed {payload.reproducibility?.seed} · fingerprint {payload.reproducibility?.config_fingerprint}</p>
            <ul className="list-disc pl-5 text-sm text-mute">
              {(payload.assumptions || []).map((item) => <li key={item}>{item}</li>)}
              {(payload.limitations || []).map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        </Panel>
      )}
      {showReport && (
        <Panel>
          <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap font-mono text-xs leading-5">{payload.report_markdown}</pre>
        </Panel>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel px-2 py-2">
      <p className="font-mono text-[10px] uppercase tracking-wider text-mute">{label}</p>
      <p className="mt-1 font-mono text-sm">{value}</p>
    </div>
  );
}

function Metric({ term, value, unit, text }: { term: string; value?: number | null; unit?: string; text?: string }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wider text-mute">{term}</dt>
      <dd>{text || (typeof value === "number" ? `${formatNumber(value, 2)} ${unit || ""}` : "—")}</dd>
    </div>
  );
}

function span(drug: Drug): string {
  const summary = drug.monte_carlo?.endpoint_summary;
  if (!summary) return "—";
  return `${formatNumber(summary.p05, 2)} to ${formatNumber(summary.p95, 2)}`;
}

function swingMax(drug?: Drug): number {
  const swings = drug?.sensitivity?.bars?.map((bar) => bar.swing) || [1];
  return Math.max(...swings, 1e-9);
}
