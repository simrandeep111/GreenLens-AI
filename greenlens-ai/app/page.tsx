'use client';

import { useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';

import CompanyForm from '@/components/intake/CompanyForm';
import UploadCard from '@/components/intake/UploadCard';
import GovernanceQuestions from '@/components/intake/GovernanceQuestions';
import { analyzeData, getBackendMeta, uploadFiles } from '@/lib/api';
import {
  clearSession,
  DEFAULT_COMPANY,
  DEFAULT_GOVERNANCE_ANSWERS,
  saveSession,
} from '@/lib/session';
import { CompanyData } from '@/lib/types';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Something went wrong while starting the analysis.';
}

export default function IntakePage() {
  const router = useRouter();
  const [isRouting, startTransition] = useTransition();
  const [company, setCompany] = useState<CompanyData>(DEFAULT_COMPANY);
  const [governanceAnswers, setGovernanceAnswers] = useState<string[]>(DEFAULT_GOVERNANCE_ANSWERS);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isBusy = isSubmitting || isRouting;
  const canSubmit =
    company.name.trim().length > 0 &&
    company.province.trim().length > 0 &&
    company.industry.trim().length > 0 &&
    company.revenue.trim().length > 0 &&
    company.employees > 0 &&
    csvFile !== null;

  const handleReset = () => {
    clearSession();
    setCompany({ ...DEFAULT_COMPANY });
    setGovernanceAnswers([...DEFAULT_GOVERNANCE_ANSWERS]);
    setCsvFile(null);
    setPdfFiles([]);
    setError(null);
  };

  const handleStartAnalysis = async () => {
    if (!canSubmit || !csvFile) {
      setError('Add a CSV file and complete the company details before starting the analysis.');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const backend = await getBackendMeta();
      const upload = await uploadFiles({
        csvFile,
        pdfFiles,
      });

      const analysis = await analyzeData({
        uploadId: upload.uploadId,
        company,
        governanceAnswers,
      });

      clearSession();
      saveSession({
        company,
        governanceAnswers,
        csvFileName: csvFile.name,
        pdfFileNames: pdfFiles.map((file) => file.name),
        uploadId: upload.uploadId,
        jobId: analysis.jobId,
        status: {
          jobId: analysis.jobId,
          status: 'queued',
          currentStep: 0,
          stepLabel: 'Queued for analysis',
          progress: 0,
          error: null,
        },
        report: null,
        backendBootId: backend.bootId,
      });

      startTransition(() => {
        router.push('/processing');
      });
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="intake-layout">
        <div className="intake-header">
          <div className="intake-eyebrow">ESG Assessment</div>
          <h1 className="intake-title">
            Submit your company<br />data for ESG analysis.
          </h1>
          <p className="intake-subtitle">
            GreenLens AI processes your operational and financial records to generate a verified ESG score,
            emissions breakdown, and compliance report aligned with Canadian reporting standards.
          </p>
          <div className="trust-bar">
            <div className="trust-item">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M8 1L2 4v4c0 3.3 2.5 5.7 6 7 3.5-1.3 6-3.7 6-7V4L8 1z"/>
              </svg>
              SOC 2 Type II
            </div>
            <div className="trust-item">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 2"/>
              </svg>
              Results in under 2 min
            </div>
            <div className="trust-item">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <rect x="3" y="2" width="10" height="12" rx="1.5"/><path d="M6 6h4M6 9h4M6 12h2"/>
              </svg>
              GHG Protocol aligned
            </div>
            <div className="trust-item">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M3 8l3 3 7-7"/>
              </svg>
              OSFI B-15 ready
            </div>
          </div>
        </div>

        <div className="form-card">
          <CompanyForm company={company} disabled={isBusy} onChange={setCompany} />
          <UploadCard
            csvFile={csvFile}
            pdfFiles={pdfFiles}
            disabled={isBusy}
            onCsvChange={setCsvFile}
            onPdfChange={setPdfFiles}
          />
          <GovernanceQuestions answers={governanceAnswers} disabled={isBusy} onChange={setGovernanceAnswers} />

          {error ? (
            <div
              style={{
                marginTop: '16px',
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

          <div className="form-footer">
            <div className="form-footer-note">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M8 1L2 4v4c0 3.3 2.5 5.7 6 7 3.5-1.3 6-3.7 6-7V4L8 1z"/>
              </svg>
              Data is encrypted in transit and at rest. We do not sell or share your information.
            </div>
            <div className="form-footer-actions">
              <button
                type="button"
                className="btn-ghost"
                onClick={handleReset}
                disabled={isBusy}
              >
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 4h10M6 4V2.8c0-.4.3-.8.8-.8h2.4c.5 0 .8.4.8.8V4M6.5 7.5v3.5M9.5 7.5v3.5M4.5 4l.6 8.1c0 .5.4.9.9.9h3.9c.5 0 .9-.4.9-.9L11.5 4"/>
                </svg>
                Reset
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleStartAnalysis}
                disabled={!canSubmit || isBusy}
                style={{ opacity: !canSubmit || isBusy ? 0.7 : 1 }}
              >
                {isBusy ? 'Starting Analysis...' : 'Begin ESG Analysis'}
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M3 8h10M9 4l4 4-4 4"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
