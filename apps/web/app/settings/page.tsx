"use client";

import { useEffect, useState } from "react";
import { Label, Panel } from "@/components/ui/panel";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  useEffect(() => {
    fetch("/api/health").then((response) => response.json()).then(setHealth).catch(() => setHealth(null));
  }, []);
  return (
    <div className="space-y-4">
      <Label>Settings</Label>
      <h1 className="font-serif text-4xl">Workspace</h1>
      <Panel>
        <p>Demo sign-in is demo@aeon7080.local / demo. Change AEON_SECRET before any shared deployment.</p>
        <p className="mt-2 font-mono text-xs text-mute">{health ? `${health.name} ${health.version}` : "API health unavailable."}</p>
      </Panel>
      <Panel>
        <p className="text-sm text-mute">Uploaded files are stored in the workspace directory with mode 600. Training on uploads does not start unless you build that path and the dataset permission allows it. This build never starts training from an upload automatically.</p>
      </Panel>
    </div>
  );
}
