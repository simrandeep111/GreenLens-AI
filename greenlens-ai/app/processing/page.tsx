'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import ProcessingSteps from '@/components/processing/ProcessingSteps';
import ProgressBar from '@/components/processing/ProgressBar';
import { getAnalysisStatus, getBackendMeta, getReport } from '@/lib/api';
import { AnalysisSession, JobStatus } from '@/lib/types';
import { loadSessionForBackend, updateSession } from '@/lib/session';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Unable to load the latest analysis status.';
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

export default function ProcessingPage() {
  const [session, setSession] = useState<AnalysisSession | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadValidatedSession = async () => {
      try {
        const backend = await getBackendMeta();
        if (cancelled) {
          return;
        }

        setSession(loadSessionForBackend(backend.bootId));
      } catch (requestError) {
        if (!cancelled) {
          setError(getErrorMessage(requestError));
          setSession(null);
        }
      }
    };

    void loadValidatedSession();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!session?.jobId || session.report) {
      return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;

    const poll = async () => {
      try {
        const nextStatus = await getAnalysisStatus(session.jobId as string);
        if (cancelled) {
          return;
        }

        const persistedStatus = updateSession({ status: nextStatus });
        setSession(persistedStatus);

        if (nextStatus.status === 'complete') {
          const report = await getReport(session.jobId as string);
          if (cancelled) {
            return;
          }

          const completedSession = updateSession({
            status: nextStatus,
            report,
          });
          setSession(completedSession);
          return;
        }

        if (nextStatus.status === 'error' || nextStatus.status === 'failed') {
          setError(nextStatus.error ?? 'The backend reported an error while generating your analysis.');
          return;
        }

        timeoutId = window.setTimeout(poll, 1500);
      } catch (requestError) {
        if (!cancelled) {
          setError(getErrorMessage(requestError));
        }
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [session?.jobId, session?.report]);

  if (session === undefined) {
    return (
      <EmptyState
        title="Loading analysis"
        description="We’re loading the latest job status from your browser session."
      />
    );
  }

  if (!session?.jobId) {
    return (
      <EmptyState
        title="No active analysis"
        description="Start a new upload first and GreenLens will create a backend job for processing."
      />
    );
  }

  const displayStatus = session.report
    ? session.status ?? buildCompleteStatus(session.jobId)
    : session.status;
  const pct = session.report ? 100 : displayStatus?.progress ?? 0;

  return (
    <div className="page-container">
      <div className="processing-layout">
        <div className="processing-orb">
          <svg viewBox="0 0 36 36" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
            <path d="M18 6 C10 6 6 11 6 18 C6 26 11.5 30 18 30 C18 30 18 24 24 20 C28 18 28 12 24 9 C22 7 20 6 18 6Z"/>
            <path d="M18 30 C18 22 24 19 28 15"/>
          </svg>
        </div>
        <h2 className="processing-title">Analysing your data</h2>
        <p className="processing-sub">
          GreenLens AI is processing your financial records, mapping emissions across all three scopes,
          validating supporting documents, and retrieving applicable Canadian compliance requirements.
        </p>

        <ProcessingSteps status={displayStatus ?? null} />
        <ProgressBar pct={pct} />

        <div className="processing-note">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
            <circle cx="8" cy="8" r="6"/><path d="M8 7v4M8 5h.01"/>
          </svg>
          {displayStatus?.stepLabel ?? 'Connecting to backend'}{displayStatus ? ` · ${displayStatus.progress}% complete` : ''}
        </div>

        {error ? (
          <div
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid #F0C8C3',
              background: 'var(--red-light)',
              color: '#7E302A',
              fontSize: '12.5px',
            }}
          >
            {error}
          </div>
        ) : null}

        <div className="processing-cta">
          {session.report ? (
            <Link href="/dashboard" className="btn-primary">
              View Dashboard
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 8h10M9 4l4 4-4 4"/>
              </svg>
            </Link>
          ) : (
            <button type="button" className="btn-primary" disabled style={{ opacity: 0.7 }}>
              Waiting for Report
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 8h10M9 4l4 4-4 4"/>
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
