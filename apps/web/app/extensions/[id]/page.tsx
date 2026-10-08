"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useToken } from "@/components/shell/session";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function ExtensionPage() {
  const token = useToken();
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<{ name: string; reason: string; status: string } | null>(null);

  useEffect(() => {
    if (!token) return;
    api<{ extensions: { id: string; name: string; reason: string; status: string }[] }>("/api/simulations/models", token)
      .then((payload) => setItem(payload.extensions.find((entry) => entry.id === params.id) || null))
      .catch(() => setItem(null));
  }, [token, params.id]);

  return (
    <div className="space-y-4">
      <Label>Extension point</Label>
      <h1 className="font-serif text-4xl">{item?.name || "Not in this build"}</h1>
      <Panel>
        <p className="font-mono text-xs text-amber">{item?.status || "DEMO / PLACEHOLDER"}</p>
        <p className="mt-3 max-w-3xl text-mute">{item?.reason || "This module is not implemented. AEON 7080 does not invent its results."}</p>
      </Panel>
    </div>
  );
}
