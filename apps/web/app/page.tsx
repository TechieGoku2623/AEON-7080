import Link from "next/link";
import { Label, Panel } from "@/components/ui/panel";

const STEPS = [
  ["Academy", "Watch how a computational experiment is framed.", "/academy"],
  ["Try the demo", "Generate a synthetic patient and run hypothetical PK/PD.", "/labs/pharmacology"],
  ["Bring a table", "Upload a permitted CSV. Training sharing stays off.", "/data/upload"],
  ["Ask the scientist", "The planner calls solvers. It does not invent numbers.", "/scientist"],
  ["Replay", "The same seed and configuration run again.", "/experiments"],
];

export default function HomePage() {
  return (
    <div className="grid-fade space-y-8">
      <section className="max-w-4xl">
        <Label>AEON 7080</Label>
        <h1 className="mt-2 font-serif text-5xl leading-tight md:text-6xl">
          A computational laboratory for simulation, data, and reproducible analysis.
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-mute">
          Simplified models, synthetic records, and an AI Scientist that can only report what the solvers return.
          This is not a medical device and it does not give clinical advice.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/labs/pharmacology" className="rounded-md bg-cyan px-4 py-2 text-sm font-medium text-ink">Open the PK/PD lab</Link>
          <Link href="/academy" className="rounded-md border border-line px-4 py-2 text-sm">Watch the academy</Link>
        </div>
      </section>
      <div className="grid gap-3 md:grid-cols-5">
        {STEPS.map(([title, text, href], index) => (
          <Link key={title} href={href}>
            <Panel className="h-full">
              <p className="font-mono text-xs text-cyan">0{index + 1}</p>
              <h2 className="mt-2 font-serif text-xl">{title}</h2>
              <p className="mt-2 text-sm text-mute">{text}</p>
            </Panel>
          </Link>
        ))}
      </div>
      <Panel>
        <Label>Five layers in this build</Label>
        <div className="mt-3 grid gap-3 md:grid-cols-5 text-sm">
          <p><strong className="block text-mist">Scientific</strong>PK/PD, glucose, circulation bookkeeping, abstract SIR/SEIR.</p>
          <p><strong className="block text-mist">Digital</strong>Seeded synthetic patients and a schematic human.</p>
          <p><strong className="block text-mist">AI</strong>Allowlisted tools, a critic, and a synthetic logistic model.</p>
          <p><strong className="block text-mist">Data</strong>Upload, profile, confirm a mapping, then simulate.</p>
          <p><strong className="block text-mist">Knowledge</strong>Academy video, chapters, transcripts, and reports without invented citations.</p>
        </div>
      </Panel>
    </div>
  );
}
