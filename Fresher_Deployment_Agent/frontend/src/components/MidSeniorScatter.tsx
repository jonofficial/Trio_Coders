import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { PyramidRow } from "../types";

interface Props {
  data: PyramidRow[];
}

export function MidSeniorScatter({ data }: Props) {
  return (
    <div className="bg-[#111118] border border-white/[0.06] rounded-xl p-5 flex flex-col h-[300px]">
      <h3 className="text-sm font-semibold text-white/90 mb-4">Mid vs Senior Concentration</h3>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis 
              type="number" 
              dataKey="midPct" 
              name="Mid %" 
              unit="%" 
              tick={{ fill: "#ffffff60", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              type="number" 
              dataKey="seniorPct" 
              name="Senior %" 
              unit="%" 
              tick={{ fill: "#ffffff60", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3', stroke: '#ffffff20' }}
              contentStyle={{ backgroundColor: "#111118", borderColor: "#ffffff10", borderRadius: "8px", fontSize: "12px" }}
              itemStyle={{ color: "#818cf8" }}
              formatter={(value: any, name: any) => [`${Number(value).toFixed(1)}%`, name]}
              labelFormatter={() => ''}
            />
            <Scatter name="Projects" data={data}>
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.overIndexedSenior ? "#f43f5e" : entry.overIndexedMid ? "#f59e0b" : "#818cf8"} 
                  opacity={0.7}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
