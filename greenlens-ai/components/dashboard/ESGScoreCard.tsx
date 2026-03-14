'use client';

import {
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  Cell,
} from 'recharts';

import { BenchmarkData, ESGScore } from '@/lib/types';

interface ESGScoreCardProps {
  score: ESGScore;
  benchmark: BenchmarkData;
}

export default function ESGScoreCard({ score, benchmark }: ESGScoreCardProps) {
  const scoreData = [
    { name: 'Score', value: score.total, fill: '#2D5A3D' },
    { name: 'Remaining', value: Math.max(100 - score.total, 0), fill: '#F1F0EC' },
  ];

  const pillars = [
    { name: 'Environmental', score: score.environmental, max: 50, color: '#2D5A3D' },
    { name: 'Social', score: score.social, max: 25, color: '#1E2B3C' },
    { name: 'Governance', score: score.governance, max: 25, color: '#B87333' },
  ];

  const deltaPct = benchmark.sectorAverage
    ? Math.round(((benchmark.sectorAverage - benchmark.yourIntensity) / benchmark.sectorAverage) * 100)
    : 0;
  const isBetterThanAverage = deltaPct >= 0;

  return (
    <div className="score-card-main">
      <div className="score-eyebrow">Overall ESG Score</div>

      <div className="score-donut-wrap">
        <ResponsiveContainer width="100%" height={160}>
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={78}
            startAngle={220}
            endAngle={-40}
            data={scoreData}
            barSize={14}
          >
            <RadialBar dataKey="value" cornerRadius={4} background={false}>
              {scoreData.map((d, i) => (
                <Cell key={i} fill={d.fill} />
              ))}
            </RadialBar>
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="score-center-val">
          <div className="score-big">{score.total}</div>
          <div className="score-grade">{score.grade}</div>
        </div>
      </div>

      <div className="score-label">{score.grade}</div>
      <div className="score-delta">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
          {isBetterThanAverage ? <path d="M8 12V4M4 8l4-4 4 4"/> : <path d="M8 4v8M4 8l4 4 4-4"/>}
        </svg>
        {Math.abs(deltaPct)}% {isBetterThanAverage ? 'lower' : 'higher'} emissions intensity vs sector average
      </div>

      <div className="score-pillars">
        {pillars.map((p) => (
          <div className="pillar-row" key={p.name}>
            <div className="pillar-dot" style={{ background: p.color }} />
            <span className="pillar-name">{p.name}</span>
            <div className="pillar-bar">
              <div
                className="pillar-fill"
                style={{ width: `${(p.score / p.max) * 100}%`, background: p.color }}
              />
            </div>
            <span className="pillar-score" style={{ color: p.color }}>
              {p.score}
              <span style={{ color: 'var(--text-tertiary)', fontSize: '10px' }}>/{p.max}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
