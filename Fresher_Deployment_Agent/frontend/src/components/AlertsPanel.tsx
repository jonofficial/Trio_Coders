import React, { useState } from "react";
import type { PyramidRow } from "../types";

interface Props {
  data: PyramidRow[];
}

type SeverityLevel = "High" | "Medium" | "Low";
type AlertType = "low-junior" | "over-senior" | "over-mid";

interface Alert {
  projectId: string;
  projectName: string;
  type: AlertType;
  label: string;
  pct: number;
  gapExcess: number;
  severity: SeverityLevel;
  fixHint: string;
  detail: string;
}

function getSeverity(gap: number): SeverityLevel {
  if (gap > 40) return "High";
  if (gap >= 20) return "Medium";
  return "Low";
}

function severityBadge(severity: SeverityLevel) {
  if (severity === "High") return <span className="text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider">High</span>;
  if (severity === "Medium") return <span className="text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider">Medium</span>;
  return <span className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider">Low</span>;
}

export function AlertsPanel({ data }: Props) {
  const [filterSeverity, setFilterSeverity] = useState<SeverityLevel | "All">("All");
  const [filterType, setFilterType] = useState<AlertType | "All">("All");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const alerts: Alert[] = [];
  for (const row of data) {
    if (row.lowJuniorWarning) {
      alerts.push({
        projectId: row.projectId,
        projectName: row.projectName,
        type: "low-junior",
        label: "Low Junior Ratio",
        pct: row.juniorPct,
        gapExcess: row.juniorGap,
        severity: getSeverity(row.juniorGap),
        fixHint: "Inject freshers to correct ratio",
        detail: `Junior headcount is at ${row.juniorPct.toFixed(1)}%, which is ${row.juniorGap.toFixed(1)}pp below the target of 79%. Deployment of entry-level talent is recommended to reduce average billing cost and maintain pyramid health.`,
      });
    }
    if (row.overIndexedSenior) {
      const excess = row.seniorPct - 1;
      alerts.push({
        projectId: row.projectId,
        projectName: row.projectName,
        type: "over-senior",
        label: "Over-Indexed Senior",
        pct: row.seniorPct,
        gapExcess: excess,
        severity: getSeverity(excess),
        fixHint: "Roll off seniors to other projects",
        detail: `Senior headcount is at ${row.seniorPct.toFixed(1)}%, which is ${excess.toFixed(1)}pp above the target limit of 1%. Consider reassigning senior staff to new engagements.`,
      });
    }
    if (row.overIndexedMid) {
      const excess = row.midPct - 20;
      alerts.push({
        projectId: row.projectId,
        projectName: row.projectName,
        type: "over-mid",
        label: "Over-Indexed Mid",
        pct: row.midPct,
        gapExcess: excess,
        severity: getSeverity(excess),
        fixHint: "Promote or reassign mid-level",
        detail: `Mid-level headcount is at ${row.midPct.toFixed(1)}%, exceeding the target maximum of 20% by ${excess.toFixed(1)}pp. Evaluate for potential senior promotions or redistribute to balance the project.`,
      });
    }
  }

  const highCount = alerts.filter(a => a.severity === "High").length;
  const medCount = alerts.filter(a => a.severity === "Medium").length;
  const lowCount = alerts.filter(a => a.severity === "Low").length;

  const filteredAlerts = alerts.filter(a => {
    if (filterSeverity !== "All" && a.severity !== filterSeverity) return false;
    if (filterType !== "All" && a.type !== filterType) return false;
    return true;
  });

  const lowJuniorAlerts = filteredAlerts.filter(a => a.type === "low-junior");
  const overSeniorAlerts = filteredAlerts.filter(a => a.type === "over-senior");
  const overMidAlerts = filteredAlerts.filter(a => a.type === "over-mid");

  const renderTable = (title: string, items: Alert[]) => {
    if (items.length === 0) return null;
    return (
      <div className="mb-8">
        <h3 className="text-sm font-semibold text-white/80 mb-3 uppercase tracking-wider">{title}</h3>
        <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-white/[0.02]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider w-1/4">Project</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Current %</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Gap/Excess</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Severity</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-white/40 uppercase tracking-wider">Fix Hint</th>
              </tr>
            </thead>
            <tbody>
              {items.map((alert, i) => {
                const isExpanded = expandedRow === `${alert.type}-${alert.projectId}`;
                return (
                  <React.Fragment key={`${alert.type}-${alert.projectId}-${i}`}>
                    <tr 
                      onClick={() => setExpandedRow(isExpanded ? null : `${alert.type}-${alert.projectId}`)}
                      className={`border-b border-white/[0.03] transition-colors cursor-pointer ${isExpanded ? "bg-white/[0.04]" : "hover:bg-white/[0.04]"}`}
                    >
                      <td className="px-4 py-3 font-medium text-white/90 truncate max-w-[200px]">
                        <div className="flex items-center gap-2">
                          <svg className={`w-3.5 h-3.5 text-white/30 transition-transform ${isExpanded ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                          <span className="truncate">{alert.projectName}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-white/80 font-mono text-xs">{alert.pct.toFixed(1)}%</td>
                      <td className="px-4 py-3 text-right font-mono text-xs text-white/60">
                        {alert.gapExcess > 0 ? "+" : ""}{alert.gapExcess.toFixed(1)}pp
                      </td>
                      <td className="px-4 py-3 text-center">{severityBadge(alert.severity)}</td>
                      <td className="px-4 py-3 text-white/60 text-xs truncate max-w-[250px]">{alert.fixHint}</td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-white/[0.01] border-b border-white/[0.03]">
                        <td colSpan={5} className="px-4 py-4 pl-10 text-xs text-white/50 leading-relaxed">
                          <strong className="text-white/70 block mb-1">Detailed Analysis:</strong>
                          {alert.detail}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (alerts.length === 0) {
    return (
      <section id="alerts-section" className="animate-fade-in">
        <h2 className="text-lg font-semibold text-white/90 mb-4 tracking-tight">Pyramid Alerts</h2>
        <div className="rounded-xl border border-emerald-500/10 bg-emerald-500/[0.03] p-8 text-center flex flex-col items-center">
          <svg className="w-8 h-8 text-emerald-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-emerald-400/90 text-sm font-medium">All projects are operating within healthy structural thresholds.</p>
        </div>
      </section>
    );
  }

  return (
    <section id="alerts-section" className="animate-fade-in flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white/90 tracking-tight">Pyramid Alerts</h2>
        
        {/* Summary Bar */}
        <div className="flex items-center gap-3 bg-[#111118] border border-white/[0.06] rounded-lg p-1.5 px-3">
          <span className="text-[10px] uppercase font-semibold text-white/40 tracking-wider mr-2">Summary:</span>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-xs font-mono text-white/80">{highCount} High</span>
          </div>
          <div className="w-px h-3 bg-white/10 mx-1" />
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="text-xs font-mono text-white/80">{medCount} Med</span>
          </div>
          <div className="w-px h-3 bg-white/10 mx-1" />
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-mono text-white/80">{lowCount} Low</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/40 font-medium">Severity:</span>
          <select 
            value={filterSeverity} 
            onChange={(e) => setFilterSeverity(e.target.value as any)}
            className="bg-[#111118] border border-white/[0.06] text-white/80 text-xs rounded-md px-2 py-1.5 outline-none focus:border-white/20"
          >
            <option value="All">All</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/40 font-medium">Type:</span>
          <select 
            value={filterType} 
            onChange={(e) => setFilterType(e.target.value as any)}
            className="bg-[#111118] border border-white/[0.06] text-white/80 text-xs rounded-md px-2 py-1.5 outline-none focus:border-white/20"
          >
            <option value="All">All Types</option>
            <option value="low-junior">Low Junior Ratio</option>
            <option value="over-senior">Over-Indexed Senior</option>
            <option value="over-mid">Over-Indexed Mid</option>
          </select>
        </div>
      </div>

      {/* Grouped Tables */}
      <div>
        {renderTable("Low Junior Ratio", lowJuniorAlerts)}
        {renderTable("Over-Indexed Senior", overSeniorAlerts)}
        {renderTable("Over-Indexed Mid", overMidAlerts)}
        
        {filteredAlerts.length === 0 && (
          <div className="text-center py-12 text-sm text-white/40 border border-white/[0.06] rounded-xl bg-white/[0.02]">
            No alerts match the selected filters.
          </div>
        )}
      </div>
    </section>
  );
}

