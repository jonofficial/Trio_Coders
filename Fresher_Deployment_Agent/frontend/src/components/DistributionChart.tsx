import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { PyramidRow } from "../types";

interface Props {
  data: PyramidRow[];
}

const COLORS = {
  healthy: "#10b981",    // emerald-500
  imbalanced: "#f59e0b", // amber-500
};

export function DistributionChart({ data }: Props) {
  const healthy = data.filter((r) => r.pyramidHealth.toLowerCase().includes("healthy")).length;
  const imbalanced = data.length - healthy;

  const chartData = [
    { name: "Healthy", value: healthy, color: COLORS.healthy },
    { name: "Imbalanced", value: imbalanced, color: COLORS.imbalanced },
  ].filter((d) => d.value > 0);

  const pct = data.length > 0 ? Math.round((healthy / data.length) * 100) : 0;

  return (
    <section id="distribution-section" className="animate-fade-in">
      <h2 className="text-base font-semibold text-white/80 mb-3">Pyramid Distribution</h2>
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 flex items-center gap-6">
        {/* Donut */}
        <div className="relative w-[100px] h-[100px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={32}
                outerRadius={46}
                startAngle={90}
                endAngle={-270}
                dataKey="value"
                strokeWidth={0}
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "#111118",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "8px",
                  color: "#fff",
                  fontSize: "12px",
                }}
                itemStyle={{ color: "rgba(255,255,255,0.7)" }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-lg font-bold text-white">{pct}%</span>
          </div>
        </div>

        {/* Legend */}
        <div className="space-y-3 flex-1">
          {[
            { label: "Healthy", value: healthy, color: "bg-emerald-500" },
            { label: "Imbalanced", value: imbalanced, color: "bg-amber-500" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${item.color}`} />
                <span className="text-xs text-white/50">{item.label}</span>
              </div>
              <span className="text-sm font-semibold text-white/80">{item.value}</span>
            </div>
          ))}
          <div className="pt-1 border-t border-white/[0.05] flex items-center justify-between">
            <span className="text-xs text-white/30">Total</span>
            <span className="text-sm font-semibold text-white/60">{data.length}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
