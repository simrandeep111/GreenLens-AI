import { FraudAnalysis, TransactionAnomaly } from '@/lib/types';
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

function anomalyIcon(anomaly: TransactionAnomaly) {
  if (anomaly.status === 'flag') {
    const color = anomaly.severity === 'high' ? '#C0392B' : anomaly.severity === 'medium' ? '#E67E22' : '#2ECC71';
    return (
      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke={color} strokeWidth="2">
        <circle cx="8" cy="8" r="6" />
        <path d="M8 5v4M8 11h.01" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="#2ECC71" strokeWidth="2">
      <path d="M3 8l3 3 7-7" />
    </svg>
  );
}

export default function DocumentAssuranceCard({ fraudAnalysis }: { fraudAnalysis: FraudAnalysis }) {
  const tone = getRiskTone(fraudAnalysis?.overallRisk ?? 'not_assessed');
  const topFlags = (fraudAnalysis?.flags ?? []).slice(0, 3);
  const anomalies = fraudAnalysis?.transactionAnomalies ?? [];
  const hasDocuments = (fraudAnalysis?.supportingDocsReviewed ?? 0) > 0 || (fraudAnalysis?.documents ?? []).length > 0;

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
            <div className="fraud-score-value">{fraudAnalysis?.riskScore ?? 0}<span>/100</span></div>
          </div>
          <div className="fraud-score-note">
            {fraudAnalysis?.supportingDocsReviewed ?? 0} document{(fraudAnalysis?.supportingDocsReviewed ?? 0) === 1 ? '' : 's'} reviewed
          </div>
        </div>

        <p className="fraud-summary-copy">{fraudAnalysis?.summary ?? 'No summary available.'}</p>

        <div className="fraud-summary-grid">
          <div className="fraud-summary-stat">
            <div className="fraud-summary-label">Verified Spend</div>
            <div className="fraud-summary-value">{formatCurrency(fraudAnalysis?.verifiedSpendAmount ?? 0)}</div>
            <div className="fraud-summary-sub">{fraudAnalysis?.verifiedSpendPct ?? 0}% of reviewed-vendor spend</div>
          </div>
          <div className="fraud-summary-stat">
            <div className="fraud-summary-label">Matched Docs</div>
            <div className="fraud-summary-value">{fraudAnalysis?.matchedDocuments ?? 0}</div>
            <div className="fraud-summary-sub">{fraudAnalysis?.partialMatches ?? 0} partial · {fraudAnalysis?.unmatchedDocuments ?? 0} unmatched</div>
          </div>
          <div className="fraud-summary-stat">
            <div className="fraud-summary-label">Duplicate Signals</div>
            <div className="fraud-summary-value">{fraudAnalysis?.duplicateDocuments ?? 0}</div>
            <div className="fraud-summary-sub">Requires manual confirmation</div>
          </div>
        </div>

        {anomalies.length > 0 && (
          <div style={{ marginTop: '14px', padding: '12px', background: 'var(--surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', color: 'var(--text-tertiary)', marginBottom: '10px' }}>
              Forensic Transaction Analysis
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {anomalies.map((anomaly) => (
                <div key={anomaly.testName} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  {anomalyIcon(anomaly)}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '12.5px', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {anomaly.testName}
                      {anomaly.status === 'flag' && (
                        <span style={{ marginLeft: '6px', fontSize: '10.5px', padding: '1px 6px', borderRadius: '3px', background: anomaly.severity === 'high' ? 'var(--red-light)' : anomaly.severity === 'medium' ? '#FFF3E0' : 'var(--green-light)', color: anomaly.severity === 'high' ? '#7E302A' : anomaly.severity === 'medium' ? '#8D4E00' : '#1B5E20' }}>
                          {anomaly.severity}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: '2px' }}>
                      {anomaly.detail.length > 120 ? anomaly.detail.slice(0, 120) + '…' : anomaly.detail}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
            {hasDocuments
              ? 'No material anomalies were detected across the uploaded supporting documents.'
              : 'No supporting documents were uploaded, so GreenLens ran ledger-only forensic checks on the CSV transactions instead.'}
          </div>
        )}
      </div>
    </div>
  );
}
