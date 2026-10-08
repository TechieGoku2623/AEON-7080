"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Menu, X } from "lucide-react";
import { SessionProvider } from "@/components/shell/session";
import { cn } from "@/lib/utils";

const GROUPS = [
  {
    label: "Laboratory",
    items: [
      { href: "/", label: "Home" },
      { href: "/scientist", label: "AI Scientist" },
      { href: "/data-scientist", label: "AI Data Scientist" },
      { href: "/demo", label: "Demo mode" },
    ],
  },
  {
    label: "Virtual world",
    items: [
      { href: "/virtual-patient", label: "Virtual patient" },
      { href: "/digital-twin", label: "Digital twin" },
    ],
  },
  {
    label: "Simulation labs",
    items: [
      { href: "/labs/physiology", label: "Physiology" },
      { href: "/labs/pharmacology", label: "Pharmacology" },
      { href: "/labs/biosignals", label: "Biosignals" },
      { href: "/labs/epidemiology", label: "Epidemiology" },
      { href: "/extensions/drug_discovery", label: "Drug discovery" },
      { href: "/extensions/genomics", label: "Genomics" },
      { href: "/extensions/imaging", label: "Imaging" },
      { href: "/extensions/clinical_trials", label: "Clinical trials" },
    ],
  },
  {
    label: "Data and experiments",
    items: [
      { href: "/data", label: "User data" },
      { href: "/data/upload", label: "Upload" },
      { href: "/experiments", label: "Experiments" },
      { href: "/experiments/builder", label: "Experiment builder" },
      { href: "/experiments/compare", label: "Compare" },
      { href: "/ml", label: "AI/ML lab" },
      { href: "/reports", label: "Reports" },
    ],
  },
  {
    label: "Knowledge",
    items: [
      { href: "/academy", label: "Academy" },
      { href: "/research", label: "Research mode" },
      { href: "/settings", label: "Settings" },
    ],
  },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <SessionProvider>
      <div className="min-h-screen md:grid md:grid-cols-[250px_1fr]">
        <aside className={cn("border-line bg-ink/95 md:border-r", open ? "block" : "hidden md:block")}>
          <div className="sticky top-0 flex max-h-screen flex-col px-4 py-5">
            <Link href="/" className="px-2" onClick={() => setOpen(false)}>
              <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-cyan">Computational laboratory</p>
              <p className="font-serif text-2xl leading-none text-mist">AEON 7080</p>
            </Link>
            <nav className="mt-6 space-y-5 overflow-y-auto pb-8">
              {GROUPS.map((group) => (
                <div key={group.label}>
                  <p className="px-2 font-mono text-[10px] uppercase tracking-[0.18em] text-mute">{group.label}</p>
                  <div className="mt-1">
                    {group.items.map((item) => {
                      const active = pathname === item.href;
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={() => setOpen(false)}
                          className={cn(
                            "block rounded-md px-2 py-1.5 text-sm text-mist/80 hover:bg-panel hover:text-mist",
                            active && "bg-panel text-cyan",
                          )}
                        >
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </aside>
        <div className="min-w-0">
          <header className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-ink/80 px-4 py-3 backdrop-blur md:px-8">
            <button className="rounded-md border border-line p-2 md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Menu">
              {open ? <X size={16} /> : <Menu size={16} />}
            </button>
            <p className="hidden font-mono text-[11px] uppercase tracking-[0.16em] text-mute md:block">
              Learn → experiment → simulate → analyze → reproduce
            </p>
            <Link href="/demo" className="rounded-full border border-amber/50 px-3 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-amber">
              Demo mode
            </Link>
          </header>
          <div className="border-b border-amber/30 bg-amber/10 px-4 py-2 text-sm text-amber md:px-8">
            SIMULATION RESULT — NOT CLINICAL EVIDENCE, DIAGNOSIS, OR MEDICAL ADVICE.
          </div>
          <main className="px-4 py-6 md:px-8 md:py-8">{children}</main>
        </div>
      </div>
    </SessionProvider>
  );
}
