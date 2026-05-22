import { useState } from "react";
import type { SuggestionRow } from "../types";
import { DownloadButton } from "./DownloadButton";

interface Props {
  data: SuggestionRow[];
  downloadUrl: string | null;
  onRowClick?: (projectId: string) => void;
}


function readinessBadge(score: number) {
  let color = "bg-zinc-500/15 text-zinc-400 border-zinc-500/20";
  if (score >= 80) color = "bg-emerald-500/15 text-emerald-400 border-emerald-500/20";
  else if (score >= 50) color = "bg-amber-500/15 text-amber-400 border-amber-500/20";
  else if (score > 0) color = "bg-red-500/15 text-red-400 border-red-500/20";

  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold border ${color}`}>
      {score > 0 ? `${score}%` : "—"}
    </span>
  );
}

export function SuggestionsTable({ data, downloadUrl, onRowClick }: Props) {
  const [minReadiness, setMinReadiness] = useState(0);
  const [search, setSearch] = useState("");

  const filtered = data.filter((row) => {
    const matchesReadiness = row.readinessScore >= minReadiness;
    const matchesSearch = 
      row.projectName.toLowerCase().includes(search.toLowerCase()) ||
      row.relevantSkills.toLowerCase().includes(search.toLowerCase()) ||
      row.trainingTrack.toLowerCase().includes(search.toLowerCase());
    return matchesReadiness && matchesSearch;
  });

  const deployable = filtered.filter((r) => r.deploymentFlag);
  const nonDeployable = filtered.filter((r) => !r.deploymentFlag);
  const sorted = [...deployable, ...nonDeployable];

  return (
    <section id="suggestions-section" className="animate-fade-in flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white/90">Deployment &amp; Training Suggestions</h2>
        <div className="flex items-center gap-4">
          {/* Filters */}
          <div className="flex items-center gap-4 bg-white/[0.02] border border-white/[0.06] rounded-lg px-3 py-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider text-white/30 font-medium">Min Readiness</span>
              <input 
                type="range" min="0" max="100" step="5"
                value={minReadiness}
                onChange={(e) => setMinReadiness(Number(e.target.value))}
                className="w-24 accent-emerald-500 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
              />
              <span className="text-xs font-mono text-emerald-400 w-8">{minReadiness}%</span>
            </div>
            <div className="w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2">
              <svg className="w-3.5 h-3.5 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input 
                type="text" 
                placeholder="Search skills or projects..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-transparent border-none text-xs text-white/80 placeholder:text-white/20 focus:ring-0 w-40"
              />
            </div>
          </div>
          <DownloadButton url={downloadUrl} label="Download Suggestions Report" />
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-white/[0.02]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Project</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Deploy?</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Intake</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Skills Needed</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Training Track</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Readiness</th>
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-white/40 text-sm">No suggestions match the filters.</td>
              </tr>
            ) : (
              sorted.map((row, i) => (
                <tr
                  key={`${row.projectId}-${i}`}
                  onClick={() => onRowClick?.(row.projectId)}
                  className={`border-b border-white/[0.03] transition-colors ${
                    onRowClick ? "cursor-pointer hover:bg-white/[0.04]" : "hover:bg-white/[0.02]"
                  } ${row.deploymentFlag ? "" : "opacity-50"}`}
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-white/90 truncate max-w-[180px]">{row.projectName}</div>
                    <div className="text-xs text-white/30 mt-0.5">Jr Gap: {row.juniorGap.toFixed(1)}pp</div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {row.deploymentFlag ? (
                      <span className="text-emerald-400 font-semibold text-xs">YES</span>
                    ) : (
                      <span className="text-white/20 text-xs">NO</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center font-mono text-white/80">
                    {row.suggestedFresherCount > 0 ? row.suggestedFresherCount : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs text-white/60 truncate max-w-[200px]" title={row.relevantSkills}>
                      {row.relevantSkills !== "N/A" ? row.relevantSkills : "—"}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs text-white/70 font-medium truncate max-w-[200px]" title={row.trainingTrack}>
                      {row.trainingTrack !== "N/A" ? row.trainingTrack : "—"}
                    </div>
                    {row.curriculumSummary !== "N/A" && (
                      <div className="text-[11px] text-white/30 truncate max-w-[200px] mt-0.5" title={row.curriculumSummary}>
                        {row.curriculumSummary}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">{readinessBadge(row.readinessScore)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

