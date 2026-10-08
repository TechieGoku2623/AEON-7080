"use client";

import { useEffect, useRef } from "react";
import katex from "katex";

export function Equation({ latex }: { latex: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    katex.render(latex, ref.current, { throwOnError: false, displayMode: false });
  }, [latex]);
  return <div ref={ref} className="overflow-x-auto" />;
}
