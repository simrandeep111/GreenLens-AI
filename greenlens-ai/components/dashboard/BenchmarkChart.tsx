'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';

import { BenchmarkData } from '@/lib/types';

interface BenchmarkChartProps {
  benchmark: BenchmarkData;
  industry: string;
}

export default function BenchmarkChart({ benchmark, industry }: BenchmarkChartProps) {
  const benchmarkData = [
    { name: 'Your Company', val: benchmark.yourIntensity },
    { name: 'Sector Average', val: benchmark.sectorAverage },
    { name: 'Top Quartile', val: benchmark.topQuartile },
  ];
  const domainMax = Math.max(...benchmarkData.map((item) => item.val), 1) * 1.2;
  const deltaPct = benchmark.sectorAverage
    ? Math.round(((benchmark.sectorAverage - benchmark.yourIntensity) / benchmark.sectorAverage) * 100)
    : 0;

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Emission Intensity vs. Benchmark</span>
        <span className="card-meta">per $1,000 revenue</span>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={120}>
          <BarChart
            data={benchmarkData}
            layout="vertical"
            margin={{ top: 0, right: 10, left: 4, bottom: 0 }}
            barSize={14}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E0D9" />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: '#9B9890', fontFamily: 'DM Sans' }}
              axisLine={false}
              tickLine={false}
              domain={[0, domainMax]}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fill: '#9B9890', fontFamily: 'DM Sans' }}
              axisLine={false}
              tickLine={false}
              width={96}
            />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: '1px solid #E2E0D9',
                borderRadius: '6px',
                fontSize: '12px',
                fontFamily: 'DM Sans',
              }}
              formatter={(v) => [String(v) + ' kgCO₂e / $1k']}
              cursor={{ fill: 'rgba(0,0,0,0.03)' }}
            />
            <Bar dataKey="val" radius={[0, 3, 3, 0]}>
              {benchmarkData.map((_, i) => (
                <Cell key={i} fill={i === 0 ? '#2D5A3D' : i === 2 ? '#4A8B5E' : '#C5CDD8'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: '12px' }}>
          Your emission intensity is{' '}
          <strong style={{ color: 'var(--text-primary)' }}>{benchmark.yourIntensity} kgCO₂e/$1,000 revenue</strong>, compared
          to a Canadian {industry} SMB average of{' '}
          <strong style={{ color: 'var(--text-primary)' }}>{benchmark.sectorAverage} kgCO₂e/$1,000</strong>. You are performing{' '}
          <strong style={{ color: 'var(--accent)' }}>{Math.abs(deltaPct)}% {deltaPct >= 0 ? 'better' : 'behind'}</strong> than sector peers.
        </p>
      </div>
    </div>
  );
}
