import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { SuggestionRow } from "../types";

interface Props {
  data: SuggestionRow[];
}

export function FresherAllocationChart({ data }: Props) {
  // Only include projects that actually have a suggested intake > 0
  const chartData = data
    .filter((r) => r.suggestedFresherCount > 0)
    .sort((a, b) => b.suggestedFresherCount - a.suggestedFresherCount)
    .slice(0, 10); // Top 10 to avoid clutter

  return (
    <div className="bg-[#111118] border border-white/[0.06] rounded-xl p-5 flex flex-col h-[300px]">
      <h3 className="text-sm font-semibold text-white/90 mb-4">Top 10 Fresher Allocations</h3>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis 
              dataKey="projectName" 
              tick={{ fill: "#ffffff60", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => val.length > 10 ? val.substring(0, 10) + '...' : val}
            />
            <YAxis 
              tick={{ fill: "#ffffff60", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip 
              cursor={{ fill: "#ffffff05" }}
              contentStyle={{ backgroundColor: "#111118", borderColor: "#ffffff10", borderRadius: "8px", fontSize: "12px" }}
              itemStyle={{ color: "#34d399" }}
            />
            <Bar dataKey="suggestedFresherCount" fill="#10b981" radius={[4, 4, 0, 0]} name="Suggested Intake" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
