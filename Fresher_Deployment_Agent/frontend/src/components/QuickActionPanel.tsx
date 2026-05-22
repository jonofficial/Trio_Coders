import type { PyramidRow } from "../types";

interface Props {
  data: PyramidRow[];
}

export function QuickActionPanel({ data }: Props) {
  if (data.length === 0) return null;

  // Highest Junior Gap
  const highestJuniorGap = [...data].sort((a, b) => b.juniorGap - a.juniorGap)[0];
  
  // Highest Senior %
  const highestSeniorPct = [...data].sort((a, b) => b.seniorPct - a.seniorPct)[0];
  
  // Lowest Junior %
  const lowestJuniorPct = [...data].sort((a, b) => a.juniorPct - b.juniorPct)[0];

  return (
    <div className="bg-[#111118] border border-white/[0.06] rounded-xl p-5 mb-8">
      <h3 className="text-sm font-semibold text-white/90 mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Actionable Insights
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/[0.02] border border-white/[0.04] rounded-lg p-4">
          <div className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-1">Highest Junior Gap</div>
          <div className="text-sm text-white/90 font-medium truncate" title={highestJuniorGap.projectName}>
            {highestJuniorGap.projectName}
          </div>
          <div className="text-xs text-white/50 mt-1">
            Missing <strong className="text-white/80">{highestJuniorGap.juniorGap.toFixed(1)}%</strong> to reach 79% target.
          </div>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.04] rounded-lg p-4">
          <div className="text-xs font-semibold text-violet-400 uppercase tracking-wider mb-1">Highest Senior %</div>
          <div className="text-sm text-white/90 font-medium truncate" title={highestSeniorPct.projectName}>
            {highestSeniorPct.projectName}
          </div>
          <div className="text-xs text-white/50 mt-1">
            Senior ratio is <strong className="text-white/80">{highestSeniorPct.seniorPct.toFixed(1)}%</strong> (Target: 1%).
          </div>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.04] rounded-lg p-4">
          <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">Lowest Junior %</div>
          <div className="text-sm text-white/90 font-medium truncate" title={lowestJuniorPct.projectName}>
            {lowestJuniorPct.projectName}
          </div>
          <div className="text-xs text-white/50 mt-1">
            Junior base is only <strong className="text-white/80">{lowestJuniorPct.juniorPct.toFixed(1)}%</strong>.
          </div>
        </div>
      </div>
    </div>
  );
}
