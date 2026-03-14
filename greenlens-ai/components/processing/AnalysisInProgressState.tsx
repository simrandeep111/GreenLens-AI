import Link from 'next/link';

import ProgressBar from '@/components/processing/ProgressBar';
import { JobStatus } from '@/lib/types';

interface AnalysisInProgressStateProps {
  title: string;
  description: string;
  status: JobStatus | null;
}

function getStatusLabel(status: JobStatus | null): string {
  if (!status) {
    return 'Connecting to backend';
  }

  if (status.status === 'complete') {
    return 'Finalizing report output';
  }

  return status.stepLabel;
}

function getDisplayProgress(status: JobStatus | null): number {
  if (!status) {
    return 0;
  }

  return status.status === 'complete' ? 99 : status.progress;
}

export default function AnalysisInProgressState({
  title,
  description,
  status,
}: AnalysisInProgressStateProps) {
  const displayProgress = getDisplayProgress(status);
  const statusLabel = getStatusLabel(status);
  const currentStep = status?.currentStep ?? 0;

  return (
    <div className="page-container">
      <div className="card analysis-pending-card">
        <div className="card-body analysis-pending-shell">
          <div className="analysis-pending-orb">
            <svg viewBox="0 0 36 36" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6 C10 6 6 11 6 18 C6 26 11.5 30 18 30 C18 30 18 24 24 20 C28 18 28 12 24 9 C22 7 20 6 18 6Z"/>
              <path d="M18 30 C18 22 24 19 28 15"/>
            </svg>
          </div>

          <div className="analysis-pending-label">Analysis In Progress</div>
          <h1 className="analysis-pending-title">{title}</h1>
          <p className="analysis-pending-subtitle">{description}</p>

          <div className="analysis-pending-meta">
            <div className="analysis-pending-pill">{statusLabel}</div>
            <div className="analysis-pending-copy">
              {currentStep > 0 ? `Step ${currentStep} of 6` : 'Preparing your ESG workflow'}
            </div>
          </div>

          <div className="analysis-pending-progress">
            <ProgressBar pct={displayProgress} />
          </div>

          <div className="analysis-pending-note">
            The page will refresh automatically once the report is ready. You can also follow the live job status
            from the processing screen.
          </div>

          <div className="analysis-pending-actions">
            <Link href="/processing" className="btn-primary">
              View Live Progress
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 8h10M9 4l4 4-4 4"/>
              </svg>
            </Link>
            <Link href="/" className="btn-ghost">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M12 8H4M8 4l-4 4 4 4"/>
              </svg>
              Back to Intake
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
