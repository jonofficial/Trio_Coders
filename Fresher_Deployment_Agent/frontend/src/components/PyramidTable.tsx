import { useState } from "react";
import type { PyramidRow } from "../types";
import { DownloadButton } from "./DownloadButton";

interface Props {
  data: PyramidRow[];
  downloadUrl: string | null;
  onRowClick?: (projectId: string) => void;
}

type FilterType = "All" | "Imbalanced" | "Low Junior" | "Healthy";

function healthBadge(status: string) {
  const isHealthy = status.toLowerCase().includes("healthy");
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
        ${isHealthy
          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
          : "bg-red-500/15 text-red-400 border border-red-500/20"
        }
      `}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? "bg-emerald-400" : "bg-red-400"}`} />
      {isHealthy ? "Healthy" : "Imbalance"}
    </span>
  );
}

function gapCell(gap: number) {
  if (gap > 5) return <span className="text-red-400 font-medium">{gap.toFixed(1)}</span>;
  if (gap > 0) return <span className="text-amber-400 font-medium">{gap.toFixed(1)}</span>;
  return <span className="text-emerald-400 font-medium">{gap.toFixed(1)}</span>;
}

function pctBar(value: number, target: number, color: string) {
  const width = Math.min(100, (value / Math.max(target, 1)) * 100);
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <span className="text-sm font-mono text-white/80 w-12 text-right">{value.toFixed(1)}%</span>
      <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export function PyramidTable({ data, downloadUrl, onRowClick }: Props) {
  const [filter, setFilter] = useState<FilterType>("All");

  const filteredData = data.filter((row) => {
    if (filter === "All") return true;
    const isHealthy = row.pyramidHealth.toLowerCase().includes("healthy");
    if (filter === "Healthy") return isHealthy;
    if (filter === "Imbalanced") return !isHealthy;
    if (filter === "Low Junior") return row.lowJuniorWarning;
    return true;
  });

  return (
    <section id="pyramid-section" className="animate-fade-in flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white/90 tracking-tight">Pyramid Health — Per Project</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] rounded-lg p-1">
            {(["All", "Imbalanced", "Low Junior", "Healthy"] as FilterType[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  filter === f ? "bg-white/10 text-white" : "text-white/40 hover:text-white/70"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <DownloadButton url={downloadUrl} label="Download Pyramid Report" />
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-white/[0.02]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Project</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">HC</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Junior %</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Mid %</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Senior %</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Jr Gap</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Mid Gap</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Sr Gap</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-white/40 text-sm">No projects match the current filter.</td>
              </tr>
            ) : (
              filteredData.map((row, i) => (
                <tr
                  key={`${row.projectId}-${i}`}
                  onClick={() => onRowClick?.(row.projectId)}
                  className={`border-b border-white/[0.03] transition-colors ${onRowClick ? "cursor-pointer hover:bg-white/[0.04]" : "hover:bg-white/[0.02]"}`}
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-white/90 truncate max-w-[200px]">{row.projectName}</div>
                    <div className="text-xs text-white/30 mt-0.5">{row.rm}</div>
                  </td>
                  <td className="px-4 py-3 text-white/60 font-mono text-xs">{row.totalHeadcount}</td>
                  <td className="px-4 py-3">{pctBar(row.juniorPct, 79, "bg-emerald-500")}</td>
                  <td className="px-4 py-3">{pctBar(row.midPct, 20, "bg-blue-500")}</td>
                  <td className="px-4 py-3">{pctBar(row.seniorPct, 1, "bg-violet-500")}</td>
                  <td className="px-4 py-3 text-center">{gapCell(row.juniorGap)}</td>
                  <td className="px-4 py-3 text-center">{gapCell(row.midGap)}</td>
                  <td className="px-4 py-3 text-center">{gapCell(row.seniorGap)}</td>
                  <td className="px-4 py-3 text-center">{healthBadge(row.pyramidHealth)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

