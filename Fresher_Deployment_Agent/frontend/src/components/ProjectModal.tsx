import { useEffect } from "react";
import type { PyramidRow, SuggestionRow } from "../types";

interface Props {
  pyramidRow?: PyramidRow;
  suggestionRow?: SuggestionRow;
  onClose: () => void;
}

export function ProjectModal({ pyramidRow, suggestionRow, onClose }: Props) {
  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!pyramidRow && !suggestionRow) return null;

  const projectName = pyramidRow?.projectName || suggestionRow?.projectName || "Unknown Project";
  const juniorGap = pyramidRow?.juniorGap ?? suggestionRow?.juniorGap ?? 0;
  
  const reasons: string[] = [];
  if (pyramidRow?.lowJuniorWarning) reasons.push("Low Junior %");
  if (pyramidRow?.overIndexedMid) reasons.push("High Mid %");
  if (pyramidRow?.overIndexedSenior) reasons.push("High Senior %");
  
  if (reasons.length === 0 && juniorGap > 0) reasons.push("Under-resourced at Junior level");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in" onClick={onClose}>
      <div 
        className="bg-[#111118] border border-white/[0.08] rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.05] flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white/90 truncate mr-4">{projectName}</h3>
          <button onClick={onClose} className="text-white/40 hover:text-white/80 transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Status block */}
          <div className="flex items-center gap-4">
            <div className="flex-1 bg-white/[0.02] border border-white/[0.04] rounded-lg p-3">
              <div className="text-xs text-white/40 mb-1 uppercase tracking-wider">Junior Gap</div>
              <div className={`text-xl font-bold ${juniorGap > 0 ? "text-amber-400" : "text-emerald-400"}`}>
                {juniorGap > 0 ? `-${juniorGap.toFixed(1)}pp` : "Healthy"}
              </div>
            </div>
            
            {suggestionRow && (
              <div className="flex-1 bg-white/[0.02] border border-white/[0.04] rounded-lg p-3">
                <div className="text-xs text-white/40 mb-1 uppercase tracking-wider">Suggested Intake</div>
                <div className="text-xl font-bold text-violet-400">
                  {suggestionRow.suggestedFresherCount > 0 ? suggestionRow.suggestedFresherCount : "None"}
                </div>
              </div>
            )}
          </div>

          {/* Why Section */}
          {reasons.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-white/80 mb-2">Why</h4>
              <ul className="list-disc list-inside text-sm text-white/60 space-y-1">
                {reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {/* Recommended Section */}
          {suggestionRow && (
            <div>
              <h4 className="text-sm font-semibold text-white/80 mb-2">Recommended</h4>
              <div className="space-y-3">
                {suggestionRow.relevantSkills && suggestionRow.relevantSkills !== "N/A" && (
                  <div>
                    <div className="text-xs text-white/40 mb-0.5">Skills Needed</div>
                    <div className="text-sm text-white/70">{suggestionRow.relevantSkills}</div>
                  </div>
                )}
                {suggestionRow.trainingTrack && suggestionRow.trainingTrack !== "N/A" && (
                  <div>
                    <div className="text-xs text-white/40 mb-0.5">Training Track</div>
                    <div className="text-sm text-white/70 font-medium">{suggestionRow.trainingTrack}</div>
                    {suggestionRow.curriculumSummary && suggestionRow.curriculumSummary !== "N/A" && (
                      <div className="text-xs text-white/40 mt-1">{suggestionRow.curriculumSummary}</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
