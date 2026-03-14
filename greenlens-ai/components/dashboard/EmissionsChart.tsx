'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

import { EmissionEntry } from '@/lib/types';

interface EmissionsChartProps {
  breakdown: EmissionEntry[];
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const tooltipFormatter = (v: any, n: any) => {
  const scopeLabel = n === 's1' ? 'Scope 1' : n === 's2' ? 'Scope 2' : 'Scope 3';
  return [String(v) + ' tCO₂e', scopeLabel];
};

export default function EmissionsChart({ breakdown }: EmissionsChartProps) {
  const emissionsData = breakdown.reduce<Array<{ cat: string; s1: number; s2: number; s3: number }>>(
    (rows, item) => {
      const existing = rows.find((row) => row.cat === item.category);
      const key = item.scope === 'Scope 1' ? 's1' : item.scope === 'Scope 2' ? 's2' : 's3';

      if (existing) {
        existing[key] += item.tCO2e;
        return rows;
      }

      rows.push({
        cat: item.category,
        s1: key === 's1' ? item.tCO2e : 0,
        s2: key === 's2' ? item.tCO2e : 0,
        s3: key === 's3' ? item.tCO2e : 0,
      });
      return rows;
    },
    [],
  );

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Emissions by Category &amp; Scope</span>
        <span className="card-meta">tCO₂e · FY 2024</span>
      </div>
      <div className="card-body">
        <div className="scope-legend">
          <div className="scope-leg-item">
            <div className="scope-dot" style={{ background: '#2D5A3D' }} />Scope 1
          </div>
          <div className="scope-leg-item">
            <div className="scope-dot" style={{ background: '#4A8B5E' }} />Scope 2
          </div>
          <div className="scope-leg-item">
            <div className="scope-dot" style={{ background: '#A8C5B4' }} />Scope 3
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={emissionsData}
            margin={{ top: 5, right: 10, left: -20, bottom: 0 }}
            barSize={28}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E0D9" />
            <XAxis
              dataKey="cat"
              tick={{ fontSize: 11, fill: '#9B9890', fontFamily: 'DM Sans' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#9B9890', fontFamily: 'DM Sans' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: '1px solid #E2E0D9',
                borderRadius: '6px',
                fontSize: '12px',
                fontFamily: 'DM Sans',
              }}
              formatter={tooltipFormatter}
              cursor={{ fill: 'rgba(0,0,0,0.03)' }}
            />
            <Bar dataKey="s1" stackId="a" fill="#2D5A3D" radius={[0, 0, 0, 0]} />
            <Bar dataKey="s2" stackId="a" fill="#4A8B5E" radius={[0, 0, 0, 0]} />
            <Bar dataKey="s3" stackId="a" fill="#A8C5B4" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
