import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { PyramidRow } from "../types";

interface Props {
  data: PyramidRow[];
}

export function GapSeverityChart({ data }: Props) {
  const ranges = {
    "0-10": 0,
    "10-20": 0,
    "20-40": 0,
    "40+": 0,
  };

  data.forEach((row) => {
    const gap = row.juniorGap;
    if (gap <= 10) ranges["0-10"]++;
    else if (gap <= 20) ranges["10-20"]++;
    else if (gap <= 40) ranges["20-40"]++;
    else ranges["40+"]++;
  });

  const chartData = [
    { name: "0–10", count: ranges["0-10"] },
    { name: "11–20", count: ranges["10-20"] },
    { name: "21–40", count: ranges["20-40"] },
    { name: "40+", count: ranges["40+"] },
  ];

  return (
    <div className="bg-[#111118] border border-white/[0.06] rounded-xl p-5 flex flex-col h-[300px]">
      <h3 className="text-sm font-semibold text-white/90 mb-4">Junior Gap Severity Distribution</h3>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis 
              dataKey="name" 
              tick={{ fill: "#ffffff60", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              tick={{ fill: "#ffffff60", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip 
              cursor={{ fill: "#ffffff05" }}
              contentStyle={{ backgroundColor: "#111118", borderColor: "#ffffff10", borderRadius: "8px", fontSize: "12px" }}
              itemStyle={{ color: "#f87171" }}
            />
            <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} name="Projects" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
