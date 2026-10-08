"use client";

import Link from "next/link";
import { Label, Panel } from "@/components/ui/panel";

export default function DataScientistPage() {
  return (
    <div className="space-y-4">
      <Label>AI Data Scientist</Label>
      <h1 className="font-serif text-4xl">Ask a loaded table</h1>
      <p className="max-w-3xl text-mute">
        Questions about missing values, associations, and trends run on the dataset page. The analyst returns the computed table, not a guessed narrative.
      </p>
      <Panel>
        <Link className="text-cyan" href="/data">Open my datasets</Link>
      </Panel>
    </div>
  );
}
