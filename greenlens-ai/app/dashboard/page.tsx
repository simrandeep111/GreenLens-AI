'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import ESGScoreCard from '@/components/dashboard/ESGScoreCard';
import EmissionsChart from '@/components/dashboard/EmissionsChart';
import ComplianceCard from '@/components/dashboard/ComplianceCard';
import RecommendationList from '@/components/dashboard/RecommendationList';
import DocumentAssuranceCard from '@/components/dashboard/DocumentAssuranceCard';
import GrantsCard from '@/components/dashboard/GrantsCard';
import BenchmarkChart from '@/components/dashboard/BenchmarkChart';
import AnalysisInProgressState from '@/components/processing/AnalysisInProgressState';
import { ApiError, getAnalysisStatus, getBackendMeta, getReport } from '@/lib/api';
import { normalizeReport } from '@/lib/report';
import { loadSessionForBackend, updateSession } from '@/lib/session';
import { AnalysisSession, JobStatus } from '@/lib/types';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Unable to load the latest dashboard data.';
}

function buildCompleteStatus(jobId: string): JobStatus {
  return {
    jobId,
    status: 'complete',
    currentStep: 7,
    stepLabel: 'Complete',
    progress: 100,
    error: null,
  };
}

function formatGeneratedDate(value: string): string {
  return new Intl.DateTimeFormat('en-CA', {
    dateStyle: 'long',
  }).format(new Date(value));
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="page-container">
      <div className="card" style={{ maxWidth: '720px', margin: '60px auto' }}>
        <div className="card-body" style={{ padding: '28px' }}>
          <div className="dash-title" style={{ fontSize: '28px', marginBottom: '8px' }}>{title}</div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: 1.7 }}>{description}</p>
          <Link href="/" className="btn-primary">
            Start New Analysis
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M3 8h10M9 4l4 4-4 4"/>
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [session, setSession] = useState<AnalysisSession | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: number | undefined;

    const loadValidatedSession = async () => {
      try {
        const backend = await getBackendMeta();
        if (cancelled) {
          return;
        }

        const stored = loadSessionForBackend(backend.bootId);
        if (!stored) {
          setSession(null);
          return;
        }

        setSession(stored);

        if (!stored.report && stored.jobId) {
          const jobId = stored.jobId;
          const status = await getAnalysisStatus(jobId);
          if (cancelled) {
            return;
          }

          const statusSession = updateSession({ status });
          setSession(statusSession);

          if (status.status === 'error' || status.status === 'failed') {
            setError(status.error ?? 'The backend reported an error while generating your dashboard.');
            return;
          }

          if (status.status !== 'complete') {
            timeoutId = window.setTimeout(loadValidatedSession, 1500);
            return;
          }

          try {
            const report = await getReport(jobId);
            if (cancelled) {
              return;
            }

            const nextSession = updateSession({
              report,
              status: buildCompleteStatus(jobId),
            });
            setSession(nextSession);
          } catch (requestError) {
            if (cancelled) {
              return;
            }

            if (requestError instanceof ApiError && requestError.status === 202) {
              timeoutId = window.setTimeout(loadValidatedSession, 1500);
              return;
            }

            setError(getErrorMessage(requestError));
          }
        }
      } catch (requestError) {
        if (cancelled) {
          return;
        }

        setError(getErrorMessage(requestError));
      }
    };

    void loadValidatedSession();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  if (session === undefined) {
    return (
      <EmptyState
        title="Loading dashboard"
        description="We’re pulling your latest ESG report from the backend."
      />
    );
  }

  if (error) {
    return (
      <EmptyState
        title="Dashboard unavailable"
        description={error}
      />
    );
  }

  if (session?.jobId && !session.report) {
    return (
      <AnalysisInProgressState
        title="Dashboard is still being prepared"
        description="Your ESG analysis is still running, so the dashboard cards are not ready to render yet."
        status={session.status}
      />
    );
  }

  if (!session?.report) {
    return (
      <EmptyState
        title="No completed analysis yet"
        description="Run an analysis first and GreenLens will populate your dashboard with live backend results."
      />
    );
  }

  const report = normalizeReport(session.report) as NonNullable<AnalysisSession['report']>;
  const company = report.company;
  const generatedDate = report.generatedAt ? formatGeneratedDate(report.generatedAt) : 'N/A';
  const pendingComplianceItems = (report.compliance ?? []).filter((item) => item.status !== 'pass').length;
  const emissions = report.emissions;
  const score = report.score;
  const fraudAnalysis = report.fraudAnalysis;

  return (
    <div className="page-container">
      <div className="dash-layout">
        <div className="dash-header">
          <div>
            <div className="dash-company-meta">
              {company.name} &nbsp;·&nbsp; <span>{company.province}</span> &nbsp;·&nbsp; {company.industry} &nbsp;·&nbsp; {company.employees} employees
            </div>
            <h1 className="dash-title">ESG Intelligence Dashboard</h1>
            <div className="dash-date">Report period: FY 2024 &nbsp;·&nbsp; Generated {generatedDate}</div>
          </div>
          <div className="dash-header-actions">
            <Link href="/" className="btn-ghost">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M12 8H4M8 4l-4 4 4 4"/>
              </svg>
              New Analysis
            </Link>
            <button className="btn-ghost" onClick={() => window.print()}>
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M8 2v9M4 8l4 4 4-4"/><path d="M2 13h12"/>
              </svg>
              Export
            </button>
            <Link href="/report" className="btn-accent">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M4 2h8l3 3v9a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/>
                <path d="M11 2v4h3"/><path d="M5 8h6M5 11h4"/>
              </svg>
              View Full Report
            </Link>
          </div>
        </div>

        <div className="score-hero-grid">
          <ESGScoreCard score={score} benchmark={emissions.benchmark} />

          <div className="kpi-right-grid">
            <div className="kpi-card accent-tint">
              <div className="kpi-label" style={{ color: '#2D5A3D' }}>
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M8 2 C5 2 2 5 2 8 C2 12 5 14 8 14 C8 14 8 10 12 8 C14 7 14 4 12 3Z"/>
                </svg>
                Total Emissions
              </div>
              <div className="kpi-value">{(emissions.totalTCO2e ?? 0).toFixed(1)}</div>
              <div className="kpi-sub">tCO₂e this fiscal year</div>
              <div className="kpi-badge green">Across 3 reporting scopes</div>
            </div>

            <div className="kpi-card navy-tint">
              <div className="kpi-label" style={{ color: '#1E2B3C' }}>
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <rect x="2" y="2" width="12" height="12" rx="1.5"/><path d="M5 8h6M5 5h6M5 11h3"/>
                </svg>
                Compliance Readiness
              </div>
              <div className="kpi-value">{report.complianceReadinessPct ?? 0}%</div>
              <div className="kpi-sub">Across assessed frameworks</div>
              <div className="kpi-badge navy">{pendingComplianceItems} actions pending</div>
            </div>

            <div className="kpi-card amber-tint">
              <div className="kpi-label" style={{ color: '#B87333' }}>
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 2"/>
                </svg>
                Grants Available
              </div>
              <div className="kpi-value">{report.totalGrantsAvailable ?? '$0'}</div>
              <div className="kpi-sub">Matched funding programs</div>
              <div className="kpi-badge amber">{(report.grants ?? []).length} eligible</div>
            </div>

            <div className="kpi-card" style={{ gridColumn: 'span 3' }}>
              <div className="kpi-label">Emission Intensity</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '1px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                {[
                  { scope: 'Scope 1 — Direct', val: emissions.scope1 ?? 0, sub: 'Owned operations and fleet' },
                  { scope: 'Scope 2 — Energy', val: emissions.scope2 ?? 0, sub: 'Purchased electricity and utilities' },
                  { scope: 'Scope 3 — Value Chain', val: emissions.scope3 ?? 0, sub: 'Supply chain, waste, and travel' },
                ].map((item) => (
                  <div key={item.scope} style={{ background: 'var(--surface)', padding: '14px 16px' }}>
                    <div style={{ fontSize: '10.5px', fontWeight: 600, color: 'var(--text-tertiary)', letterSpacing: '0.5px', textTransform: 'uppercase', marginBottom: '6px' }}>{item.scope}</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '20px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '2px' }}>
                      {(item.val ?? 0).toFixed(1)} <span style={{ fontSize: '12px', fontWeight: 400, color: 'var(--text-tertiary)' }}>tCO₂e</span>
                    </div>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>{item.sub}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="dash-main-grid">
          <div className="dash-left">
            <EmissionsChart breakdown={emissions.breakdown ?? []} />
            <ComplianceCard items={report.compliance ?? []} readinessPct={report.complianceReadinessPct ?? 0} />
            <div className="card">
              <div className="card-header"><span className="card-title">Company Overview</span></div>
              <div className="card-body">
                <div className="company-stat-grid">
                  {[
                    { label: 'Business Name', val: company.name },
                    { label: 'Annual Revenue', val: company.revenue },
                    { label: 'Employees', val: `${company.employees} FTE` },
                    { label: 'Province', val: company.province },
                    { label: 'Industry', val: company.industry },
                    { label: 'Report Standard', val: 'GHG Protocol' },
                  ].map((stat) => (
                    <div className="co-stat" key={stat.label}>
                      <div className="co-stat-label">{stat.label}</div>
                      <div className="co-stat-val">{stat.val}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <BenchmarkChart benchmark={emissions.benchmark} industry={company.industry} />
          </div>
          <div className="dash-right">
            <RecommendationList recommendations={report.recommendations ?? []} />
            <DocumentAssuranceCard fraudAnalysis={fraudAnalysis} />
            <GrantsCard grants={report.grants ?? []} />
          </div>
        </div>
      </div>
    </div>
  );
}
