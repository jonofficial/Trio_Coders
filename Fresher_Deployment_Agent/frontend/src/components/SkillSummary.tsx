import type { SuggestionRow } from "../types";

interface Props {
  data: SuggestionRow[];
}

/**
 * Extracts and ranks the top N skills from comma-separated skill strings
 * across all suggestions rows.
 */
function getTopSkills(rows: SuggestionRow[], topN = 5): { skill: string; count: number }[] {
  const freq: Record<string, number> = {};

  for (const row of rows) {
    const sources = [row.relevantSkills, row.skillsCovered, row.primarySkills];
    for (const src of sources) {
      if (!src || src === "N/A") continue;
      const skills = src.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean);
      for (const skill of skills) {
        freq[skill] = (freq[skill] ?? 0) + 1;
      }
    }
  }

  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
    .map(([skill, count]) => ({ skill, count }));
}

export function SkillSummary({ data }: Props) {
  const skills = getTopSkills(data);

  if (skills.length === 0) {
    return (
      <section id="skill-summary-section" className="animate-fade-in">
        <h2 className="text-base font-semibold text-white/80 mb-3">Top Demanded Skills</h2>
        <p className="text-xs text-white/30">No skill data available</p>
      </section>
    );
  }

  const maxCount = skills[0].count;

  return (
    <section id="skill-summary-section" className="animate-fade-in">
      <h2 className="text-base font-semibold text-white/80 mb-3">Top Demanded Skills</h2>
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2.5">
        {skills.map(({ skill, count }, i) => {
          const barWidth = Math.round((count / maxCount) * 100);
          return (
            <div key={skill} className="flex items-center gap-3">
              <span className="text-xs text-white/25 font-mono w-4 shrink-0">{i + 1}</span>
              <span className="text-xs font-medium text-white/70 w-[110px] shrink-0 truncate" title={skill}>
                {skill}
              </span>
              <div className="flex-1 h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-500"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              <span className="text-[11px] text-white/30 font-mono w-4 shrink-0 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
