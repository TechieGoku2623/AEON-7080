"use client";

import Link from "next/link";
import { Label, Panel } from "@/components/ui/panel";

export default function ReportsPage() {
  return (
    <div className="space-y-4">
      <Label>Reports</Label>
      <h1 className="font-serif text-4xl">Scientific reports</h1>
      <Panel>
        <p className="text-mute">A report is stored with each completed experiment and quotes that run. It does not add citations.</p>
        <Link className="mt-3 inline-block text-cyan" href="/experiments">Open experiments</Link>
      </Panel>
    </div>
  );
}
