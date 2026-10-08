"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function AcademyPage() {
  const token = useToken();
  const [videos, setVideos] = useState<any[]>([]);
  const [query, setQuery] = useState("PK/PD");
  const [hits, setHits] = useState<any[] | null>(null);

  useEffect(() => {
    if (!token) return;
    api<{ videos: any[] }>("/api/academy/videos", token).then((payload) => setVideos(payload.videos));
  }, [token]);

  async function search() {
    if (!token) return;
    const payload = await api<{ hits: any[] }>(`/api/academy/search?q=${encodeURIComponent(query)}`, token);
    setHits(payload.hits);
  }

  const featured = videos[0];
  return (
    <div className="space-y-4">
      <Label>Academy</Label>
      <h1 className="font-serif text-4xl">AEON 7080 Academy</h1>
      {featured && (
        <Panel className="grid gap-4 md:grid-cols-[220px_1fr] md:items-center">
          <img src={featured.thumbnail_url} alt="" className="h-32 w-full rounded-md object-cover" />
          <div>
            <Label>Featured</Label>
            <h2 className="font-serif text-3xl">{featured.title}</h2>
            <p className="mt-2 text-sm text-mute">{featured.description}</p>
            <div className="mt-3 flex gap-2">
              <Link className="rounded-md bg-cyan px-3 py-2 text-sm text-ink" href={`/academy/${featured.id}`}>Watch now</Link>
              {featured.template_id && <Link className="rounded-md border border-line px-3 py-2 text-sm" href="/labs/pharmacology">Try demo</Link>}
            </div>
          </div>
        </Panel>
      )}
      <Panel>
        <div className="flex gap-2">
          <input className="flex-1 rounded border border-line bg-ink px-2 py-1" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="rounded border border-line px-3" onClick={search}>Search</button>
        </div>
        {hits && (
          <ul className="mt-3 space-y-2 text-sm">
            {hits.map((hit) => (
              <li key={hit.video.id}><Link className="text-cyan" href={`/academy/${hit.video.id}`}>{hit.video.title}</Link> {hit.transcript && <span className="text-mute">— {hit.transcript}</span>}</li>
            ))}
          </ul>
        )}
      </Panel>
      <div className="grid gap-3 md:grid-cols-2">
        {videos.map((video) => (
          <Link key={video.id} href={`/academy/${video.id}`}>
            <Panel>
              <p className="font-mono text-[10px] uppercase text-mute">{video.category}</p>
              <h2 className="font-serif text-2xl">{video.title}</h2>
              <p className="text-sm text-mute">{video.duration}s</p>
            </Panel>
          </Link>
        ))}
      </div>
    </div>
  );
}
