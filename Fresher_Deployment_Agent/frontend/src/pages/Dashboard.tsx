import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { usePipeline } from "../hooks/usePipeline";
import { Sidebar } from "../components/Sidebar";
import { RunPipelineButton } from "../components/RunPipelineButton";
import { SummaryCards } from "../components/SummaryCards";
import { PyramidTable } from "../components/PyramidTable";
import { AlertsPanel } from "../components/AlertsPanel";
import { SuggestionsTable } from "../components/SuggestionsTable";
import { ProjectModal } from "../components/ProjectModal";
import { QuickActionPanel } from "../components/QuickActionPanel";
import { FresherAllocationChart } from "../components/FresherAllocationChart";
import { GapSeverityChart } from "../components/GapSeverityChart";
import { MidSeniorScatter } from "../components/MidSeniorScatter";
import { TopIssuesTable } from "../components/TopIssuesTable";
import { DistributionChart } from "../components/DistributionChart";
import { SkillSummary } from "../components/SkillSummary";

// Sidebar width in pixels — must match Sidebar component widths
const SIDEBAR_EXPANDED = 200;
const SIDEBAR_COLLAPSED = 56;

export function Dashboard() {
  const {
    status, error, pyramidData, suggestionsData, summary,
    pyramidPath, suggestionsPath,
    run, reset,
  } = usePipeline();

  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_EXPANDED);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "analysis">("overview");
  const hasResults = status === "success";

  function handleSidebarCollapse(collapsed: boolean) {
    setSidebarWidth(collapsed ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED);
  }

  const openModal = (projectId: string) => setSelectedProjectId(projectId);
  const closeModal = () => setSelectedProjectId(null);

  const selectedPyramidRow = pyramidData.find(r => r.projectId === selectedProjectId);
  const selectedSuggestionRow = suggestionsData.find(r => r.projectId === selectedProjectId);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex">
      <Sidebar
        hasResults={hasResults}
        onCollapseChange={handleSidebarCollapse}
      />

      <div
        className="flex-1 flex flex-col min-h-screen transition-all duration-300"
        style={{ marginLeft: `${sidebarWidth}px` }}
      >
        <header className="border-b border-white/[0.06] bg-[#0a0a0f]/80 backdrop-blur-xl sticky top-0 z-30">
          <div className="px-6 py-3.5 flex items-center justify-between">
            <div>
              <h1 className="text-sm font-semibold tracking-tight text-white/90">Fresher Deployment Agent</h1>
              <p className="text-[10px] text-white/25">Workforce Pyramid Analysis Dashboard</p>
            </div>
            <RunPipelineButton status={status} onRun={run} onReset={reset} />
          </div>
        </header>

        <main className="flex-1 px-6 py-8">
          {status === "idle" && (
            <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/10 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-emerald-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-white/80 mb-2">Ready to Analyze</h2>
              <p className="text-sm text-white/30 max-w-md text-center leading-relaxed">
                Click <strong className="text-white/50">Run Pipeline</strong> to process RIS & SO data,
                evaluate workforce pyramid ratios, and generate deployment recommendations.
              </p>
            </div>
          )}

          {status === "loading" && (
            <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
              <div className="relative w-16 h-16 mb-6">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 animate-pulse" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-7 h-7 text-emerald-400 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" className="opacity-20" />
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-white/80 mb-2">Processing Pipeline</h2>
              <p className="text-sm text-white/30 max-w-md text-center">
                Ingesting → Validating → Aggregating → Running rules → Generating reports…
              </p>
              <div className="mt-6 w-48 h-1 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full animate-progress" />
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/10 flex items-center justify-center mb-6">
                <span className="text-2xl">✕</span>
              </div>
              <h2 className="text-xl font-semibold text-red-400 mb-2">Pipeline Failed</h2>
              <p className="text-sm text-white/40 max-w-lg text-center font-mono bg-white/[0.03] rounded-lg px-4 py-3 border border-white/[0.06]">
                {error}
              </p>
            </div>
          )}

          {status === "success" && summary && (
            <>
              <Routes>
                <Route path="/" element={
                  <div className="space-y-8 animate-fade-in">
                    <SummaryCards summary={summary} />
                    <QuickActionPanel data={pyramidData} />

                    <div className="flex items-center gap-2 border-b border-white/[0.06] pb-4">
                      <button
                        onClick={() => setActiveTab("overview")}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === "overview" ? "bg-white/10 text-white" : "text-white/40 hover:text-white/70 hover:bg-white/[0.02]"}`}
                      >
                        Overview
                      </button>
                      <button
                        onClick={() => setActiveTab("analysis")}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === "analysis" ? "bg-white/10 text-white" : "text-white/40 hover:text-white/70 hover:bg-white/[0.02]"}`}
                      >
                        Analysis
                      </button>
                    </div>

                    <div className="animate-fade-in">
                      {activeTab === "overview" && (
                        <div className="space-y-6">
                          <TopIssuesTable data={pyramidData} />
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <DistributionChart data={pyramidData} />
                            <SkillSummary data={suggestionsData} />
                          </div>
                        </div>
                      )}

                      {activeTab === "analysis" && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <GapSeverityChart data={pyramidData} />
                          <MidSeniorScatter data={pyramidData} />
                          <div className="md:col-span-2">
                            <FresherAllocationChart data={suggestionsData} />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                } />


                <Route path="/pyramid" element={
                  <div className="animate-fade-in">
                    <PyramidTable
                      data={pyramidData}
                      downloadUrl={pyramidPath}
                      onRowClick={openModal}
                    />
                  </div>
                } />

                <Route path="/alerts" element={
                  <div className="animate-fade-in">
                    <AlertsPanel data={pyramidData} />
                  </div>
                } />

                <Route path="/suggestions" element={
                  <div className="animate-fade-in">
                    <SuggestionsTable
                      data={suggestionsData}
                      downloadUrl={suggestionsPath}
                      onRowClick={openModal}
                    />
                  </div>
                } />

                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>

              <ProjectModal
                pyramidRow={selectedPyramidRow}
                suggestionRow={selectedSuggestionRow}
                onClose={closeModal}
              />
            </>
          )}
        </main>

        <footer className="border-t border-white/[0.04] px-6 py-3 text-center text-[11px] text-white/15">
          FDA v1.0 — Pyramid Target: 79% Junior / 20% Mid / 1% Senior
        </footer>
      </div>
    </div>
  );
}

