import Link from "next/link";
import { Label, Panel } from "@/components/ui/panel";

const DEMOS: { index: string; title: string; href: string; ready: boolean }[] = [
  { index: "01", title: "Virtual patient", href: "/virtual-patient", ready: true },
  { index: "02", title: "Drug response", href: "/labs/pharmacology", ready: true },
  { index: "03", title: "Cardiovascular", href: "/labs/physiology", ready: true },
  { index: "04", title: "Glucose", href: "/labs/physiology", ready: true },
  { index: "05", title: "ECG + model", href: "/labs/biosignals", ready: true },
  { index: "06", title: "Drug discovery", href: "/extensions/drug_discovery", ready: false },
  { index: "07", title: "Genomics", href: "/extensions/genomics", ready: false },
  { index: "08", title: "Medical imaging", href: "/extensions/imaging", ready: false },
  { index: "09", title: "Epidemiology", href: "/labs/epidemiology", ready: true },
  { index: "10", title: "Clinical trial", href: "/extensions/clinical_trials", ready: false },
  { index: "11", title: "AI Scientist", href: "/scientist", ready: true },
  { index: "12", title: "Upload your own data", href: "/data/upload", ready: true },
];

export default function DemoPage() {
  return (
    <div className="space-y-4">
      <Label>Demo mode</Label>
      <h1 className="font-serif text-4xl">Twelve entry points</h1>
      <p className="max-w-3xl text-mute">Ready demos run the solvers. The others are labeled extension points and do not show fabricated output.</p>
      <div className="grid gap-3 md:grid-cols-2">
        {DEMOS.map((demo) => (
          <Link key={demo.index} href={demo.href}>
            <Panel>
              <p className="font-mono text-xs text-cyan">{demo.index} · {demo.ready ? "Ready" : "DEMO / PLACEHOLDER"}</p>
              <h2 className="font-serif text-2xl">{demo.title}</h2>
            </Panel>
          </Link>
        ))}
      </div>
    </div>
  );
}
