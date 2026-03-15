'use client';

import { useState } from 'react';

import { ESGScore } from '@/lib/types';

const NAV_ITEMS = [
  { id: 'exec', label: 'Executive Summary' },
  { id: 'emissions', label: 'Emissions Overview' },
  { id: 'compliance', label: 'Compliance & Regulatory' },
  { id: 'funding', label: 'Funding Opportunities' },
  { id: 'actions', label: 'Recommended Actions' },
];

interface ReportSidebarProps {
  score: ESGScore;
}

export default function ReportSidebar({ score }: ReportSidebarProps) {
  const [activeId, setActiveId] = useState('exec');

  const scrollTo = (id: string) => {
    const el = document.getElementById('section-' + id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setActiveId(id);
  };

  return (
    <div className="report-rail">
      <div className="report-nav">
        <div className="report-nav-title">Contents</div>
        <div className="report-nav-items">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`report-nav-item ${activeId === item.id ? 'active' : ''}`}
              onClick={() => scrollTo(item.id)}
            >
              <div className="report-nav-item-dot" />
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="report-score-card">
        <div style={{ fontSize: '10.5px', fontWeight: 600, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: '10px' }}>Overall Score</div>
        <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: '32px', letterSpacing: '-0.5px', color: 'var(--text-primary)', lineHeight: 1 }}>{score.total}</div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>out of 100 · {score.grade}</div>
        <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Environmental</span>
            <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{score.environmental}/50</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Social</span>
            <span style={{ color: 'var(--navy)', fontWeight: 600 }}>{score.social}/25</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Governance</span>
            <span style={{ color: 'var(--amber)', fontWeight: 600 }}>{score.governance}/25</span>
          </div>
        </div>
      </div>
    </div>
  );
}
