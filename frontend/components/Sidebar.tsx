"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  ShieldCheck,
  Database,
  FileClock,
  BookOpen,
  Sparkles
} from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/ask", label: "Ask", icon: Search },
  { href: "/admin", label: "Knowledge", icon: Database },
  { href: "/logs", label: "Audit Logs", icon: FileClock },
  { href: "/about", label: "Methodology", icon: BookOpen }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-[260px] shrink-0 flex-col gap-6 p-5 border-r border-white/5 bg-black/30 backdrop-blur-xl sticky top-0 h-screen">
      <Link href="/" className="flex items-center gap-3 px-2 pt-2">
        <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 via-violet-500 to-cyan-400 flex items-center justify-center shadow-glow">
          <ShieldCheck className="text-white" size={20} />
          <span className="absolute inset-0 rounded-xl ring-1 ring-white/20" />
        </div>
        <div>
          <div className="text-white font-semibold tracking-tight leading-none">HALT-RAG</div>
          <div className="text-[11px] text-white/50 mt-1">Trust-Aware RAG</div>
        </div>
      </Link>

      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname?.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx("nav-link", active && "active")}
            >
              <Icon size={16} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto glass rounded-2xl p-4 text-xs text-white/70 leading-relaxed">
        <div className="flex items-center gap-2 mb-2 text-white">
          <Sparkles size={14} className="text-accent-cyan" />
          <span className="font-semibold tracking-tight">Probabilistic, not Oracle</span>
        </div>
        The detector is a <span className="text-white">probabilistic trust signal</span> — multiple
        independent signals are combined; disagreement decreases confidence.
      </div>
    </aside>
  );
}
