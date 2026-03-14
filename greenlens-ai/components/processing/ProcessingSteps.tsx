'use client';

import { JobStatus } from '@/lib/types';

type StepState = 'pending' | 'running' | 'done';

interface Step {
  id: number;
  name: string;
  desc: string;
}

const STEPS: Step[] = [
  { id: 1, name: 'Parsing uploaded data', desc: 'Structuring the uploaded CSV into validated transaction records.' },
  { id: 2, name: 'Normalizing merchants and categories', desc: 'Cleaning vendor names and mapping spend into consistent categories.' },
  { id: 3, name: 'Classifying Scope 1 / 2 / 3', desc: 'Assigning each activity to the right GHG Protocol reporting scope.' },
  { id: 4, name: 'Calculating emissions and benchmarks', desc: 'Applying Canadian emission factors and sector intensity benchmarks.' },
  { id: 5, name: 'Retrieving compliance and grant context', desc: 'Matching regulations and funding programs to your province and sector.' },
  { id: 6, name: 'Verifying supporting documents and fraud signals', desc: 'Reviewing uploaded bills, receipts, and invoices against the ledger for evidence gaps and anomalies.' },
  { id: 7, name: 'Generating ESG report', desc: 'Building the dashboard, recommendations, narrative report, and document-assurance output.' },
];

function StepIcon({ state }: { state: StepState }) {
  if (state === 'done') {
    return (
      <div className="step-icon done">
        <svg viewBox="0 0 16 16" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round">
          <path d="M3 8l3 3 7-7"/>
        </svg>
      </div>
    );
  }
  if (state === 'running') {
    return (
      <div className="step-icon active-state">
        <svg viewBox="0 0 16 16" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round">
          <circle cx="8" cy="8" r="4"/><path d="M8 2v2M8 12v2M2 8h2M12 8h2"/>
        </svg>
      </div>
    );
  }
  return (
    <div className="step-icon pending">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
        <path d="M8 2v12M2 8h12" opacity="0.4"/>
      </svg>
    </div>
  );
}

function StepStatus({ state }: { state: StepState }) {
  if (state === 'done') return <div className="step-status done">Complete</div>;
  if (state === 'running') {
    return (
      <div className="step-status running">
        <div className="spinner"/>
        Running
      </div>
    );
  }
  return <div className="step-status queued">Queued</div>;
}

interface ProcessingStepsProps {
  status: JobStatus | null;
}

function getStepState(stepId: number, status: JobStatus | null): StepState {
  if (!status) {
    return stepId === 1 ? 'running' : 'pending';
  }

  if (status.status === 'complete') {
    return 'done';
  }

  if (stepId < status.currentStep) {
    return 'done';
  }

  if (stepId === status.currentStep) {
    return 'running';
  }

  return 'pending';
}

export default function ProcessingSteps({ status }: ProcessingStepsProps) {
  return (
    <div className="steps-container">
      {STEPS.map((step) => {
        const stepState = getStepState(step.id, status);

        return (
        <div
          key={step.id}
          className={`step-row ${stepState === 'done' ? 'completed' : stepState === 'running' ? 'active' : ''}`}
        >
          <StepIcon state={stepState} />
          <div className="step-info">
            <div className="step-name">{step.name}</div>
            <div className="step-desc">{step.desc}</div>
          </div>
          <StepStatus state={stepState} />
        </div>
        );
      })}
    </div>
  );
}
