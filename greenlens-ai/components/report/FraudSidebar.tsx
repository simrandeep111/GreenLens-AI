'use client';

import { useState } from 'react';

import { FraudAnalysis } from '@/lib/types';

const NAV_ITEMS = [
  { id: 'fraud', label: 'Fraud Overview' },
  { id: 'fraud-forensic', label: 'Forensic Tests' },
  { id: 'fraud-flags', label: 'Flagged Findings' },
  { id: 'fraud-documents', label: 'Documents Reviewed' },
];

function getRiskTone(risk: string) {
  if (risk === 'high') {
    return { badgeClass: 'high', label: 'High Risk' };
  }
  if (risk === 'medium') {
    return { badgeClass: 'medium', label: 'Medium Risk' };
  }
  if (risk === 'not_assessed') {
    return { badgeClass: 'neutral', label: 'Not Assessed' };
  }
  return { badgeClass: 'low', label: 'Low Risk' };
}

export default function FraudSidebar({ fraudAnalysis }: { fraudAnalysis: FraudAnalysis }) {
  const [activeId, setActiveId] = useState('fraud');
  const flaggedAnomalies = (fraudAnalysis.transactionAnomalies ?? []).filter((item) => item.status === 'flag').length;
  const tone = getRiskTone(fraudAnalysis.overallRisk);

  const scrollTo = (id: string) => {
    const el = document.getElementById(`section-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    setActiveId(id);
  };

  return (
    <div className="report-rail">
      <div className="report-nav">
        <div className="report-nav-title">Fraud Detection</div>
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

      <div className="report-score-card fraud-side-card">
        <div className="fraud-side-top">
          <div>
            <div className="fraud-side-label">Risk Snapshot</div>
            <div className="fraud-side-score">{fraudAnalysis.riskScore}<span>/100</span></div>
          </div>
          <div className={`fraud-severity-badge ${tone.badgeClass}`}>{tone.label}</div>
        </div>

        <div className="fraud-side-meta">
          <div>
            <span>Documents reviewed</span>
            <strong>{fraudAnalysis.supportingDocsReviewed}</strong>
          </div>
          <div>
            <span>Open flags</span>
            <strong>{fraudAnalysis.flags.length}</strong>
          </div>
          <div>
            <span>Forensic anomalies</span>
            <strong>{flaggedAnomalies}</strong>
          </div>
        </div>

        <p className="fraud-side-summary">{fraudAnalysis.summary}</p>
      </div>
    </div>
  );
}
