"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useToken } from "@/components/shell/session";
import { Button } from "@/components/ui/button";
import { Label, Panel } from "@/components/ui/panel";
import { api } from "@/lib/api";

export default function VideoPage() {
  const token = useToken();
  const params = useParams<{ id: string }>();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [video, setVideo] = useState<any>(null);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (!token) return;
    api(`/api/academy/videos/${params.id}`, token).then(setVideo);
  }, [token, params.id]);

  useEffect(() => {
    if (!token || !videoRef.current) return;
    const element = videoRef.current;
    const onTime = () => {
      api(`/api/academy/videos/${params.id}/progress`, token, {
        method: "POST",
        body: JSON.stringify({ position_seconds: element.currentTime, completed: element.ended }),
      }).catch(() => undefined);
    };
    element.addEventListener("pause", onTime);
    element.addEventListener("ended", onTime);
    return () => {
      element.removeEventListener("pause", onTime);
      element.removeEventListener("ended", onTime);
    };
  }, [token, params.id, video]);

  if (!video) return <p>Loading the lesson…</p>;
  return (
    <div className="grid gap-4 lg:grid-cols-[1.4fr_0.6fr]">
      <div className="space-y-3">
        <Label>{video.category}</Label>
        <h1 className="font-serif text-4xl">{video.title}</h1>
        <video
          ref={videoRef}
          className="aspect-video w-full rounded-xl bg-black"
          controls
          src={video.video_url}
          onRateChange={(event) => setSpeed(event.currentTarget.playbackRate)}
        >
          <track kind="captions" src={`/api/academy/videos/${video.id}/captions`} srcLang="en" label="English" default />
        </video>
        <div className="flex flex-wrap gap-2 text-sm">
          {[0.75, 1, 1.25, 1.5].map((rate) => (
            <button key={rate} className={`rounded border px-2 py-1 ${speed === rate ? "border-cyan text-cyan" : "border-line"}`} onClick={() => { if (videoRef.current) { videoRef.current.playbackRate = rate; setSpeed(rate); } }}>{rate}×</button>
          ))}
          <button className="rounded border border-line px-2 py-1" onClick={() => videoRef.current?.requestFullscreen()}>Fullscreen</button>
          {video.template_id && <Link href="/labs/pharmacology"><Button type="button" variant="ghost">Try this experiment</Button></Link>}
        </div>
      </div>
      <div className="space-y-3">
        <Panel>
          <Label>Chapters</Label>
          <ul className="mt-2 space-y-1 text-sm">
            {video.chapters.map((chapter: any) => (
              <li key={chapter.title}>
                <button className="text-left text-cyan" onClick={() => { if (videoRef.current) videoRef.current.currentTime = chapter.start_seconds; }}>
                  {format(chapter.start_seconds)} {chapter.title}
                </button>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel>
          <Label>Transcript</Label>
          <ul className="mt-2 space-y-2 text-sm">
            {video.transcript.map((line: any) => (
              <li key={line.start_seconds}>
                <button className="text-left" onClick={() => { if (videoRef.current) videoRef.current.currentTime = line.start_seconds; }}>
                  <span className="mr-2 font-mono text-xs text-mute">{format(line.start_seconds)}</span>
                  {line.text}
                </button>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

function format(seconds: number) {
  const s = Math.floor(seconds);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}
