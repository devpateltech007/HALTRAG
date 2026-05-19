import { ReactNode } from "react";

export function SectionHeader({
  icon,
  title,
  subtitle,
  right
}: {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
      <div className="flex items-center gap-3 min-w-0">
        {icon && (
          <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-white tracking-tight leading-tight">
            {title}
          </h2>
          {subtitle && <p className="text-[12px] text-white/50 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {right}
    </div>
  );
}
