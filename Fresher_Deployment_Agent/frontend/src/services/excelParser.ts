import * as XLSX from "xlsx";
import type { PyramidRow, SuggestionRow, SummaryMetrics } from "../types";

// ── Column name normalizers ────────────────────────────────────────────
// The exporter uses human-readable column names like "Project Name / Account Name".
// We normalize them to our internal type keys.

const PYRAMID_COL_MAP: Record<string, keyof PyramidRow> = {
  "project id": "projectId",
  "project name / account name": "projectName",
  "project name": "projectName",
  "rm": "rm",
  "total active headcount": "totalHeadcount",
  "junior count": "juniorCount",
  "mid count": "midCount",
  "senior count": "seniorCount",
  "junior %": "juniorPct",
  "mid %": "midPct",
  "senior %": "seniorPct",
  "junior gap (79 − actual%)": "juniorGap",
  "junior gap": "juniorGap",
  "mid gap": "midGap",
  "senior gap": "seniorGap",
  "low junior warning": "lowJuniorWarning",
  "over-indexed mid": "overIndexedMid",
  "over-indexed senior": "overIndexedSenior",
  "pyramid health status": "pyramidHealth",
  "audit run date": "auditDate",
};

const SUGGESTIONS_COL_MAP: Record<string, keyof SuggestionRow> = {
  "project id": "projectId",
  "project name / account name": "projectName",
  "project name": "projectName",
  "rm": "rm",
  "junior %": "juniorPct",
  "junior gap": "juniorGap",
  "pyramid health status": "pyramidHealth",
  "deployment opportunity flag": "deploymentFlag",
  "suggested fresher intake count": "suggestedFresherCount",
  "relevant technologies": "relevantSkills",
  "primary skills present": "primarySkills",
  "training track name": "trainingTrack",
  "curriculum summary": "curriculumSummary",
  "skills covered": "skillsCovered",
  "training suggestion flag": "trainingFlag",
  "deployment readiness score": "readinessScore",
  "audit run date": "auditDate",
};

function normalizeKey(raw: string): string {
  return raw.trim().toLowerCase().replace(/\s+/g, " ");
}

function toBool(val: unknown): boolean {
  if (typeof val === "boolean") return val;
  const s = String(val ?? "").trim().toLowerCase();
  return s === "yes" || s === "true" || s === "1";
}

function toNum(val: unknown): number {
  const n = Number(val);
  return isNaN(n) ? 0 : n;
}

// ── Parse raw sheet JSON into typed rows ───────────────────────────────

function mapRow<T>(raw: Record<string, unknown>, colMap: Record<string, keyof T>): Partial<T> {
  const mapped: Record<string, unknown> = {};
  for (const [rawKey, rawVal] of Object.entries(raw)) {
    const normalized = normalizeKey(rawKey);
    const targetKey = colMap[normalized];
    if (targetKey) {
      mapped[targetKey as string] = rawVal;
    }
  }
  return mapped as Partial<T>;
}

// ── Public parsers ─────────────────────────────────────────────────────

export function parsePyramidExcel(buffer: ArrayBuffer): PyramidRow[] {
  const wb = XLSX.read(buffer, { type: "array" });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rawRows: Record<string, unknown>[] = XLSX.utils.sheet_to_json(sheet);

  return rawRows.map((raw) => {
    const m = mapRow<PyramidRow>(raw, PYRAMID_COL_MAP);
    return {
      projectId: String(m.projectId ?? "N/A"),
      projectName: String(m.projectName ?? "Unknown"),
      rm: String(m.rm ?? "N/A"),
      totalHeadcount: toNum(m.totalHeadcount),
      juniorCount: toNum(m.juniorCount),
      midCount: toNum(m.midCount),
      seniorCount: toNum(m.seniorCount),
      juniorPct: toNum(m.juniorPct),
      midPct: toNum(m.midPct),
      seniorPct: toNum(m.seniorPct),
      juniorGap: toNum(m.juniorGap),
      midGap: toNum(m.midGap),
      seniorGap: toNum(m.seniorGap),
      lowJuniorWarning: toBool(m.lowJuniorWarning),
      overIndexedMid: toBool(m.overIndexedMid),
      overIndexedSenior: toBool(m.overIndexedSenior),
      pyramidHealth: String(m.pyramidHealth ?? "Unknown"),
      auditDate: String(m.auditDate ?? ""),
    };
  });
}

export function parseSuggestionsExcel(buffer: ArrayBuffer): SuggestionRow[] {
  const wb = XLSX.read(buffer, { type: "array" });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rawRows: Record<string, unknown>[] = XLSX.utils.sheet_to_json(sheet);

  return rawRows.map((raw) => {
    const m = mapRow<SuggestionRow>(raw, SUGGESTIONS_COL_MAP);
    return {
      projectId: String(m.projectId ?? "N/A"),
      projectName: String(m.projectName ?? "Unknown"),
      rm: String(m.rm ?? "N/A"),
      juniorPct: toNum(m.juniorPct),
      juniorGap: toNum(m.juniorGap),
      pyramidHealth: String(m.pyramidHealth ?? "Unknown"),
      deploymentFlag: toBool(m.deploymentFlag),
      suggestedFresherCount: toNum(m.suggestedFresherCount),
      relevantSkills: String(m.relevantSkills ?? "N/A"),
      primarySkills: String(m.primarySkills ?? "N/A"),
      trainingTrack: String(m.trainingTrack ?? "N/A"),
      curriculumSummary: String(m.curriculumSummary ?? "N/A"),
      skillsCovered: String(m.skillsCovered ?? "N/A"),
      trainingFlag: toBool(m.trainingFlag),
      readinessScore: toNum(m.readinessScore),
      auditDate: String(m.auditDate ?? ""),
    };
  });
}

// ── Compute summary from parsed data ──────────────────────────────────

export function computeSummary(
  pyramid: PyramidRow[],
  suggestions: SuggestionRow[]
): SummaryMetrics {
  const totalProjects = pyramid.length;
  const avgJuniorPct =
    totalProjects > 0
      ? Math.round(
          (pyramid.reduce((sum, r) => sum + r.juniorPct, 0) / totalProjects) * 100
        ) / 100
      : 0;
  const alertCount = pyramid.filter(
    (r) => r.lowJuniorWarning || r.overIndexedMid || r.overIndexedSenior
  ).length;
  const deploymentOpportunities = suggestions.filter(
    (r) => r.deploymentFlag
  ).length;
  const totalHeadcount = pyramid.reduce((sum, r) => sum + r.totalHeadcount, 0);
  const healthyProjects = pyramid.filter(
    (r) => r.pyramidHealth.toLowerCase().includes("healthy")
  ).length;

  // Health score: blend of healthy-project ratio + junior ratio proximity to target (79%)
  const healthRatio = totalProjects > 0 ? healthyProjects / totalProjects : 0;
  const juniorScore = Math.max(0, 1 - Math.abs(avgJuniorPct - 79) / 79);
  const healthScore = Math.round((healthRatio * 0.6 + juniorScore * 0.4) * 100);

  // Total freshers needed across all deployable projects
  const totalFreshersNeeded = suggestions
    .filter((r) => r.deploymentFlag)
    .reduce((sum, r) => sum + r.suggestedFresherCount, 0);

  // Headcount Efficiency: % of total headcount in imbalanced projects
  // Wait, requirement says: "% of total headcount in imbalanced projects". Let's name it headcountEfficiency (or imbalancedHeadcountPct)
  // Re-reading logic: "Sum headcount where status = 'Imbalance'. Divide by total headcount."
  const imbalancedHeadcount = pyramid
    .filter((r) => !r.pyramidHealth.toLowerCase().includes("healthy"))
    .reduce((sum, r) => sum + r.totalHeadcount, 0);
  const headcountEfficiency = totalHeadcount > 0 ? (imbalancedHeadcount / totalHeadcount) * 100 : 0;


  return {
    totalProjects,
    avgJuniorPct,
    alertCount,
    deploymentOpportunities,
    totalHeadcount,
    healthyProjects,
    healthScore,
    totalFreshersNeeded,
    headcountEfficiency,
  };
}
