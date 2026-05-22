import type { SummaryMetrics } from "../types";

interface Props {
  summary: SummaryMetrics;
}

interface CardDef {
  id: string;
  label: string;
  value: string | number;
  accent: string;
  icon: React.ReactNode;
}

export function SummaryCards({ summary }: Props) {
  const cards: CardDef[] = [
    {
      id: "total-projects",
      label: "Total Projects",
      value: summary.totalProjects,
      accent: "from-blue-500/20 to-blue-600/5 border-blue-500/20",
      icon: (
        <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
        </svg>
      ),
    },

    {
      id: "avg-junior",
      label: "Avg Junior %",
      value: `${summary.avgJuniorPct}%`,
      accent: summary.avgJuniorPct >= 70
        ? "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20"
        : "from-amber-500/20 to-amber-600/5 border-amber-500/20",
      icon: (
        <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      ),
    },
    {
      id: "alert-count",
      label: "Alerts",
      value: summary.alertCount,
      accent: summary.alertCount > 0
        ? "from-red-500/20 to-red-600/5 border-red-500/20"
        : "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20",
      icon: (
        <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      ),
    },

    {
      id: "freshers-needed",
      label: "Freshers Needed",
      value: summary.totalFreshersNeeded,
      accent: summary.totalFreshersNeeded > 0
        ? "from-indigo-500/20 to-indigo-600/5 border-indigo-500/20"
        : "from-zinc-500/20 to-zinc-600/5 border-zinc-500/20",
      icon: (
        <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      ),
    },
    {
      id: "total-headcount",
      label: "Headcount",
      value: summary.totalHeadcount,
      accent: "from-cyan-500/20 to-cyan-600/5 border-cyan-500/20",
      icon: (
        <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
        </svg>
      ),
    },

    {
      id: "headcount-efficiency",
      label: "Imbalance HC %",
      value: `${summary.headcountEfficiency.toFixed(1)}%`,
      accent: summary.headcountEfficiency < 20
        ? "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20"
        : "from-red-500/20 to-red-600/5 border-red-500/20",
      icon: (
        <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
        </svg>
      ),
    }
  ];

  return (
    <section id="summary-section" className="animate-fade-in">
      <h2 className="text-lg font-semibold text-white/90 mb-4 tracking-tight">Pipeline Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {cards.map((card) => (
          <div
            key={card.id}
            id={card.id}
            className={`relative rounded-xl border p-4 bg-gradient-to-br ${card.accent} backdrop-blur-sm transition-all duration-300 hover:scale-[1.02]`}
          >
            <div className="mb-2 opacity-70">{card.icon}</div>
            <div className="text-xl font-bold text-white tracking-tight mb-0.5">{card.value}</div>
            <div className="text-[10px] font-medium text-white/40 uppercase tracking-wider">{card.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
