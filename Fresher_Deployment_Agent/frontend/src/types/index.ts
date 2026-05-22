// ── Pipeline API response ──────────────────────────────────────────────
export interface PipelineResponse {
  pyramid_path: string | null;
  suggestions_path: string | null;
}


// ── Pyramid Report row (parsed from Excel) ────────────────────────────
export interface PyramidRow {
  projectId: string;
  projectName: string;
  rm: string;
  totalHeadcount: number;
  juniorCount: number;
  midCount: number;
  seniorCount: number;
  juniorPct: number;
  midPct: number;
  seniorPct: number;
  juniorGap: number;
  midGap: number;
  seniorGap: number;
  lowJuniorWarning: boolean;
  overIndexedMid: boolean;
  overIndexedSenior: boolean;
  pyramidHealth: string;
  auditDate: string;
}

// ── Suggestions Report row (parsed from Excel) ────────────────────────
export interface SuggestionRow {
  projectId: string;
  projectName: string;
  rm: string;
  juniorPct: number;
  juniorGap: number;
  pyramidHealth: string;
  deploymentFlag: boolean;
  suggestedFresherCount: number;
  relevantSkills: string;
  primarySkills: string;
  trainingTrack: string;
  curriculumSummary: string;
  skillsCovered: string;
  trainingFlag: boolean;
  readinessScore: number;
  auditDate: string;
}

// ── Derived summary metrics ───────────────────────────────────────────
export interface SummaryMetrics {
  totalProjects: number;
  avgJuniorPct: number;
  alertCount: number;
  deploymentOpportunities: number;
  totalHeadcount: number;
  healthyProjects: number;
  healthScore: number;        // 0–100 composite score
  totalFreshersNeeded: number; // sum of suggested fresher intake
  headcountEfficiency: number; // % of headcount not in imbalance
}

// ── Active sidebar section ────────────────────────────────────────────
export type SidebarSection = "dashboard" | "pyramid" | "alerts" | "suggestions";

// ── Pipeline state machine ────────────────────────────────────────────
export type PipelineStatus = "idle" | "loading" | "success" | "error";

export interface PipelineState {
  status: PipelineStatus;
  error: string | null;
  pyramidData: PyramidRow[];
  suggestionsData: SuggestionRow[];
  summary: SummaryMetrics | null;
}
