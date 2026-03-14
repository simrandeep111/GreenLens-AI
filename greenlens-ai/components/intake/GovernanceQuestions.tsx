'use client';

export const GOVERNANCE_QUESTIONS = [
  {
    question: 'Does your company have a formal diversity & inclusion policy?',
    options: ['Yes', 'In Progress', 'No'],
  },
  {
    question: 'Do all employees receive benefits above provincial minimum standards?',
    options: ['Yes', 'Partial', 'No'],
  },
  {
    question: 'Does your company publish an annual financial or sustainability report?',
    options: ['No', 'Yes', 'Planned'],
  },
  {
    question: 'Is there a documented data privacy and security policy?',
    options: ['Yes', 'In Progress', 'No'],
  },
];

interface GovernanceQuestionsProps {
  answers: string[];
  disabled?: boolean;
  onChange: (answers: string[]) => void;
}

export default function GovernanceQuestions({
  answers,
  disabled = false,
  onChange,
}: GovernanceQuestionsProps) {
  const safeAnswers = GOVERNANCE_QUESTIONS.map((question, index) => answers[index] ?? question.options[0]);

  return (
    <div className="form-section">
      <div className="form-section-label">
        Governance Self-Assessment
        <div className="form-section-num">3</div>
      </div>
      <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        These five indicators inform your Social and Governance sub-scores. All responses are confidential.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {GOVERNANCE_QUESTIONS.map((q, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '11px 14px',
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{q.question}</span>
            <select
              className="form-select"
              style={{ width: '110px', flexShrink: 0 }}
              value={safeAnswers[i]}
              disabled={disabled}
              onChange={(e) => {
                const next = [...safeAnswers];
                next[i] = e.target.value;
                onChange(next);
              }}
            >
              {q.options.map((opt) => (
                <option key={opt}>{opt}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
