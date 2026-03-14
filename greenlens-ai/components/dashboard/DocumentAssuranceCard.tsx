import { FraudAnalysis } from '@/lib/types';
import { formatCurrency } from '@/lib/utils';

function getRiskTone(risk: string) {
  if (risk === 'high') {
    return {
      badgeClass: 'high',
      label: 'High Risk',
    };
  }

  if (risk === 'medium') {
    return {
      badgeClass: 'medium',
      label: 'Medium Risk',
    };
  }

  if (risk === 'not_assessed') {
    return {
      badgeClass: 'neutral',
      label: 'Not Assessed',
    };
  }

  return {
    badgeClass: 'low',
    label: 'Low Risk',
  };
}

export default function DocumentAssuranceCard({ fraudAnalysis }: { fraudAnalysis: FraudAnalysis }) {
  const tone = getRiskTone(fraudAnalysis.overallRisk);
  const topFlags = fraudAnalysis.flags.slice(0, 3);

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Supporting Document Assurance</span>
        <span className={`fraud-severity-badge ${tone.badgeClass}`}>{tone.label}</span>
      </div>
      <div className="card-body">
        <div className="fraud-score-row">
          <div>
            <div className="fraud-score-label">Fraud / evidence risk score</div>
            <div className="fraud-score-value">{fraudAnalysis.riskScore}<span>/100</span></div>
          </div>
          <div className="fraud-score-note">
            {fraudAnalysis.supportingDocsReviewed} document{fraudAnalysis.supportingDocsReviewed === 1 ? '' : 's'} reviewed
          </div>
        </div>

        <p className="fraud-summary-copy">{fraudAnalysis.summary}</p>

        <div className="fraud-summary-grid">
          <div className="fraud-summary-stat">
            <div className="fraud-summary-label">Verified Spend</div>
            <div className="fraud-summary-value">{formatCurrency(fraudAnalysis.verifiedSpendAmount)}</div>
            <div className="fraud-summary-sub">{fraudAnalysis.verifiedSpendPct}% of reviewed-vendor spend</div>
          </div>
          <div className="fraud-summary-stat">
            <div className="fraud-summary-label">Matched Docs</div>
            <div className="fraud-summary-value">{fraudAnalysis.matchedDocuments}</div>
            <div className="fraud-summary-sub">{fraudAnalysis.partialMatches} partial · {fraudAnalysis.unmatchedDocuments} unmatched</div>
          </div>
          <div className="fraud-summary-stat">
            <div className="fraud-summary-label">Duplicate Signals</div>
            <div className="fraud-summary-value">{fraudAnalysis.duplicateDocuments}</div>
            <div className="fraud-summary-sub">Requires manual confirmation</div>
          </div>
        </div>

        {topFlags.length > 0 ? (
          <div className="fraud-flag-list">
            {topFlags.map((flag) => (
              <div className="fraud-flag-item" key={`${flag.category}-${flag.title}`}>
                <div className={`fraud-flag-dot ${flag.severity}`} />
                <div>
                  <div className="fraud-flag-title">{flag.title}</div>
                  <div className="fraud-flag-detail">{flag.detail}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="fraud-empty-note">
            No material anomalies were detected across the uploaded supporting documents.
          </div>
        )}
      </div>
    </div>
  );
}
