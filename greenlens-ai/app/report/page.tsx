'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import AnalysisInProgressState from '@/components/processing/AnalysisInProgressState';
import ReportSidebar from '@/components/report/ReportSidebar';
import ReportCopilot from '@/components/report/ReportCopilot';
import ReportSection from '@/components/report/ReportSection';
import EmissionsTable from '@/components/report/EmissionsTable';
import { ApiError, getAnalysisStatus, getBackendMeta, getReport } from '@/lib/api';
import { loadSessionForBackend, updateSession } from '@/lib/session';
import { AnalysisSession, ComplianceItem, JobStatus } from '@/lib/types';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Unable to load the full report.';
}

function buildCompleteStatus(jobId: string): JobStatus {
  return {
    jobId,
    status: 'complete',
    currentStep: 6,
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

function splitParagraphs(text: string): string[] {
  return text
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
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

function getComplianceStatusCopy(status: ComplianceItem['status']) {
  if (status === 'pass') {
    return {
      label: 'Compliant',
      statusBg: 'var(--accent)',
      bg: 'var(--accent-light)',
      border: '#C8DDD0',
    };
  }

  if (status === 'warn') {
    return {
      label: 'Attention Needed',
      statusBg: 'var(--amber)',
      bg: 'var(--amber-light)',
      border: '#E8D4BB',
    };
  }

  return {
    label: 'Gap Identified',
    statusBg: 'var(--red-soft)',
    bg: 'var(--red-light)',
    border: '#F0C8C3',
  };
}

export default function ReportPage() {
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
            setError(status.error ?? 'The backend reported an error while generating your report.');
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
        title="Loading report"
        description="We’re pulling your latest ESG report from the backend."
      />
    );
  }

  if (error) {
    return (
      <EmptyState
        title="Report unavailable"
        description={error}
      />
    );
  }

  if (session?.jobId && !session.report) {
    return (
      <AnalysisInProgressState
        title="Full ESG report is still being generated"
        description="We’re still assembling the narrative report sections, tables, and citations for this analysis."
        status={session.status}
      />
    );
  }

  if (!session?.report) {
    return (
      <EmptyState
        title="No report available yet"
        description="Complete an analysis first and GreenLens will generate a full narrative report here."
      />
    );
  }

  const report = session.report;
  const chatJobId = session.jobId ?? session.status?.jobId ?? null;
  const generatedDate = formatGeneratedDate(report.generatedAt);
  const executiveParagraphs = splitParagraphs(report.reportSections.executiveSummary);
  const emissionsParagraphs = splitParagraphs(report.reportSections.emissionsNarrative);
  const complianceParagraphs = splitParagraphs(report.reportSections.complianceNarrative);
  const fundingParagraphs = splitParagraphs(report.reportSections.fundingNarrative);
  const actionParagraphs = splitParagraphs(report.reportSections.actionsNarrative);

  return (
    <div className="page-container">
      <div className="report-layout">
        <div className="report-header">
          <div className="report-title-area">
            <div className="report-doc-label">ESG Intelligence Report</div>
            <h1 className="report-title">
              {report.company.name}<br />
              Environmental, Social &amp; Governance Assessment
            </h1>
            <p className="report-subtitle">
              FY 2024 · Generated by GreenLens AI · Aligned with GHG Protocol, GRI Standards, and OSFI B-15
            </p>
            <div className="report-meta-row">
              <div className="report-meta-item"><strong>Reference:</strong> {report.reportId}</div>
              <div className="report-meta-item"><strong>Score:</strong> {report.score.total} / 100</div>
              <div className="report-meta-item"><strong>Generated:</strong> {generatedDate}</div>
              <div className="report-meta-item"><strong>Standard:</strong> GHG Protocol Corporate</div>
            </div>
          </div>
          <div className="report-actions">
            <Link href="/dashboard" className="btn-ghost">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
                <path d="M12 8H4M8 4l-4 4 4 4"/>
              </svg>
              Back to Dashboard
            </Link>
            <button className="btn-accent" onClick={() => window.print()}>
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
                <path d="M8 2v9M4 8l4 4 4-4"/><path d="M2 13h12"/>
              </svg>
              Download PDF
            </button>
          </div>
        </div>

        <div className="report-grid">
          <ReportSidebar score={report.score} />

          <div className="report-body">
            <ReportSection id="exec" num="01" eyebrow="Executive Summary" title="Executive Summary">
              {executiveParagraphs.map((paragraph) => (
                <p className="report-p" key={paragraph}>{paragraph}</p>
              ))}
              <div className="report-callout">
                <div className="report-callout-label">Key Metrics</div>
                {report.emissions.totalTCO2e.toFixed(1)} tCO₂e total emissions · {report.complianceReadinessPct}% compliance readiness · {report.totalGrantsAvailable} in matched grants
              </div>
            </ReportSection>

            <ReportSection id="emissions" num="02" eyebrow="Emissions Overview" title="Emissions Overview">
              {emissionsParagraphs.map((paragraph) => (
                <p className="report-p" key={paragraph}>{paragraph}</p>
              ))}
              <EmissionsTable breakdown={report.emissions.breakdown} total={report.emissions.totalTCO2e} />
              <p className="report-p">
                Verified emissions intensity is <strong>{report.emissions.intensityKgPerRevenue.toFixed(1)} kgCO₂e per $1,000 revenue</strong>,
                compared with a sector average of <strong>{report.emissions.benchmark.sectorAverage} kgCO₂e</strong> and a top quartile threshold of{' '}
                <strong>{report.emissions.benchmark.topQuartile} kgCO₂e</strong>.
              </p>
            </ReportSection>

            <ReportSection id="compliance" num="03" eyebrow="Compliance & Regulatory Insights" title="Compliance & Regulatory Insights">
              {complianceParagraphs.map((paragraph) => (
                <p className="report-p" key={paragraph}>{paragraph}</p>
              ))}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', margin: '16px 0' }}>
                {report.compliance.map((item) => {
                  const statusCopy = getComplianceStatusCopy(item.status);

                  return (
                    <ComplianceFramework
                      key={item.framework}
                      title={item.framework}
                      status={statusCopy.label}
                      statusBg={statusCopy.statusBg}
                      bg={statusCopy.bg}
                      border={statusCopy.border}
                      detail={item.detail}
                    />
                  );
                })}
              </div>
            </ReportSection>

            <ReportSection id="funding" num="04" eyebrow="Funding Opportunities" title="Funding & Grants Opportunities">
              {fundingParagraphs.map((paragraph) => (
                <p className="report-p" key={paragraph}>{paragraph}</p>
              ))}
              <div className="action-list">
                {report.grants.map((grant, index) => (
                  <ActionItem
                    key={grant.name}
                    num={`G${index + 1}`}
                    numBg="var(--accent)"
                    title={grant.name}
                    detail={grant.description}
                    tags={grant.tags.map((tag, tagIndex) => ({
                      label: tag,
                      type: tagIndex === 0 ? 'timeline' : tagIndex === 1 ? 'impact' : 'cost',
                    }))}
                  />
                ))}
              </div>
            </ReportSection>

            <ReportSection id="actions" num="05" eyebrow="Recommended Actions" title="Recommended Next Actions">
              {actionParagraphs.map((paragraph) => (
                <p className="report-p" key={paragraph}>{paragraph}</p>
              ))}
              <div className="action-list">
                {report.recommendations.map((recommendation, index) => (
                  <ActionItem
                    key={`${recommendation.text}-${index}`}
                    num={String(index + 1)}
                    title={recommendation.text}
                    detail={`Expected impact: ${recommendation.impactLabel}.`}
                    tags={[
                      { label: recommendation.impactLabel, type: 'impact' },
                    ]}
                  />
                ))}
              </div>
            </ReportSection>

            <div className="report-footer">
              <div className="report-footer-left">
                This report was generated by GreenLens AI on {generatedDate}.<br />
                Reference: {report.reportId} · GHG Protocol Corporate Standard · GRI Standards · OSFI B-15
              </div>
              <div className="report-footer-actions">
                <Link href="/dashboard" className="btn-ghost">
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
                    <path d="M12 8H4M8 4l-4 4 4 4"/>
                  </svg>
                  Back to Dashboard
                </Link>
                <button className="btn-accent" onClick={() => window.print()}>
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
                    <path d="M8 2v9M4 8l4 4 4-4"/><path d="M2 13h12"/>
                  </svg>
                  Download PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ReportCopilot jobId={chatJobId} companyName={report.company.name} />
    </div>
  );
}

function ComplianceFramework({
  title, status, statusBg, bg, border, detail,
}: {
  title: string;
  status: string;
  statusBg: string;
  bg: string;
  border: string;
  detail: string;
}) {
  return (
    <div style={{ padding: '16px 20px', border: `1px solid ${border}`, background: bg, borderRadius: 'var(--radius-sm)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
        <div style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--text-primary)' }}>{title}</div>
        <div style={{ fontSize: '11px', fontWeight: 600, background: statusBg, color: 'white', padding: '3px 9px', borderRadius: '4px', whiteSpace: 'nowrap' }}>{status}</div>
      </div>
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{detail}</p>
    </div>
  );
}

function ActionItem({
  num,
  numBg = 'var(--navy)',
  title,
  detail,
  tags,
}: {
  num: string;
  numBg?: string;
  title: string;
  detail: string;
  tags: Array<{ label: string; type: 'timeline' | 'impact' | 'cost' }>;
}) {
  return (
    <div className="action-item">
      <div className="action-num" style={{ background: numBg }}>{num}</div>
      <div>
        <div className="action-title">{title}</div>
        <div className="action-detail">{detail}</div>
        {tags.length > 0 ? (
          <div className="action-tags">
            {tags.map((tag) => (
              <div key={`${num}-${tag.label}`} className={`action-tag ${tag.type}`}>
                {tag.label}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
