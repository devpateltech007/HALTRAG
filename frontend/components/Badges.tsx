import clsx from "clsx";
import type { Risk, HallucinationType } from "@/lib/api";
import { AlertTriangle, CheckCircle2, ShieldAlert, Sparkles } from "lucide-react";

const RISK_LABEL: Record<Risk, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk"
};

export function RiskBadge({ risk }: { risk: Risk }) {
  const cls =
    risk === "low"
      ? "badge badge-low"
      : risk === "medium"
      ? "badge badge-medium"
      : "badge badge-high";
  const Icon = risk === "low" ? CheckCircle2 : risk === "medium" ? AlertTriangle : ShieldAlert;
  return (
    <span className={cls}>
      <Icon size={12} /> {RISK_LABEL[risk]}
    </span>
  );
}

const TYPE_TONE: Record<HallucinationType, string> = {
  faithful: "badge-low",
  factual: "badge-high",
  contextual: "badge-medium",
  reasoning: "badge-violet"
};

export function TypeBadge({ type }: { type: HallucinationType }) {
  return (
    <span className={clsx("badge", TYPE_TONE[type] ?? "badge-neutral")}>
      <Sparkles size={12} /> {type}
    </span>
  );
}

export function LabelBadge({ label }: { label: "grounded" | "uncertain" | "hallucinated" }) {
  const tone =
    label === "grounded" ? "badge-low" : label === "uncertain" ? "badge-medium" : "badge-high";
  return <span className={clsx("badge", tone)}>{label}</span>;
}
