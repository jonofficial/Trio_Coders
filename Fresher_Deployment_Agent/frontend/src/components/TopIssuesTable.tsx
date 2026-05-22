import type { PyramidRow } from "../types";

interface Props {
  data: PyramidRow[];
}

export function TopIssuesTable({ data }: Props) {
  // Top 5 projects sorted by highest junior gap (most under-resourced first)
  const top5 = [...data]
    .filter((r) => r.juniorGap > 0)
    .sort((a, b) => b.juniorGap - a.juniorGap)
    .slice(0, 5);

  if (top5.length === 0) {
    return (
      <section id="top-issues-section" className="animate-fade-in">
        <h2 className="text-base font-semibold text-white/80 mb-3">Top Problem Projects</h2>
        <div className="rounded-xl border border-emerald-500/10 bg-emerald-500/[0.03] p-5 text-center text-sm text-emerald-400/60">
          No junior-deficit projects found
        </div>
      </section>
    );
  }

  return (
    <section id="top-issues-section" className="animate-fade-in">
      <h2 className="text-base font-semibold text-white/80 mb-3">Top Problem Projects</h2>
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-white/30 uppercase tracking-wider">#</th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-white/30 uppercase tracking-wider">Project</th>
              <th className="text-right px-4 py-2.5 text-xs font-semibold text-white/30 uppercase tracking-wider">Junior %</th>
              <th className="text-right px-4 py-2.5 text-xs font-semibold text-white/30 uppercase tracking-wider">Gap</th>
            </tr>
          </thead>
          <tbody>
            {top5.map((row, i) => {
              const severity =
                row.juniorGap > 40 ? "text-red-400" :
                row.juniorGap > 20 ? "text-amber-400" :
                "text-white/50";
              return (
                <tr key={row.projectId || i} className="border-b border-white/[0.03] last:border-0 hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-2.5 text-white/20 text-xs font-mono">{i + 1}</td>
                  <td className="px-4 py-2.5">
                    <span className="text-white/80 font-medium truncate block max-w-[160px]" title={row.projectName}>
                      {row.projectName}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-white/60 text-xs">{row.juniorPct.toFixed(1)}%</td>
                  <td className={`px-4 py-2.5 text-right font-mono text-xs font-semibold ${severity}`}>
                    -{row.juniorGap.toFixed(1)}pp
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
