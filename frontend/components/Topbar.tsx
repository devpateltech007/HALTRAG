"use client";

import { useEffect, useState } from "react";
import { Activity, Cpu, Database, Radio } from "lucide-react";
import { healthCheck } from "@/lib/api";

type Status = "connected" | "checking" | "down";

export default function Topbar() {
  const [backend, setBackend] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const res = await healthCheck();
        if (!cancelled) setBackend(res.status === "ok" ? "connected" : "down");
      } catch {
        if (!cancelled) setBackend("down");
      }
    }
    check();
    const interval = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 px-6 lg:px-10 py-4 border-b border-white/5 bg-black/30 backdrop-blur-xl">
      <div className="flex items-center gap-2 lg:hidden">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 via-violet-500 to-cyan-400" />
        <span className="font-semibold tracking-tight">HALT-RAG</span>
      </div>

      <div className="hidden md:flex items-center gap-2 text-[12px] text-white/60">
        <span className="opacity-80">/</span>
        <span>HALT-RAG</span>
        <span className="opacity-40">·</span>
        <span>Trust-Aware Retrieval-Augmented Generation</span>
      </div>

      <div className="flex items-center gap-2 flex-wrap justify-end">
        <StatusPill
          icon={<Radio size={12} />}
          label={
            backend === "connected"
              ? "Backend connected"
              : backend === "checking"
              ? "Connecting…"
              : "Backend offline"
          }
          tone={backend === "connected" ? "ok" : backend === "down" ? "err" : "warn"}
        />
        <StatusPill icon={<Activity size={12} />} label="Detector active" tone="ok" />
        <StatusPill icon={<Database size={12} />} label="Dynamic updates" tone="ok" />
        <StatusPill icon={<Cpu size={12} />} label="Provider active" tone="ok" />
      </div>
    </header>
  );
}

function StatusPill({
  icon,
  label,
  tone
}: {
  icon: React.ReactNode;
  label: string;
  tone: "ok" | "warn" | "err";
}) {
  const dotClass =
    tone === "ok" ? "pill-dot" : tone === "warn" ? "pill-dot warn" : "pill-dot err";
  return (
    <div className="pill">
      <span className={dotClass} />
      <span className="text-white/80 flex items-center gap-1.5">
        <span className="text-white/60">{icon}</span>
        {label}
      </span>
    </div>
  );
}
