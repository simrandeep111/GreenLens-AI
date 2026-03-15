import { FraudAnalysis } from '@/lib/types';
import { formatCurrency } from '@/lib/utils';

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

function formatMatchStatus(status: string) {
  if (status === 'matched') return 'Matched';
  if (status === 'partial') return 'Partial';
  if (status === 'unmatched') return 'Unmatched';
  return status;
}

interface SupportingDocumentsSectionProps {
  fraudAnalysis: FraudAnalysis;
  sectionIdPrefix?: string;
}

function buildSectionId(prefix: string | undefined, suffix: string) {
  return prefix ? `section-${prefix}-${suffix}` : undefined;
}

export default function SupportingDocumentsSection({
  fraudAnalysis,
  sectionIdPrefix,
}: SupportingDocumentsSectionProps) {
  const tone = getRiskTone(fraudAnalysis?.overallRisk ?? 'not_assessed');
  const flags = fraudAnalysis?.flags ?? [];
  const documents = fraudAnalysis?.documents ?? [];
  const anomalies = fraudAnalysis?.transactionAnomalies ?? [];
  const hasDocuments = (fraudAnalysis?.supportingDocsReviewed ?? 0) > 0 || documents.length > 0;

  return (
    <div className="fraud-report-shell" id={buildSectionId(sectionIdPrefix, 'overview')}>
      <div className="fraud-report-hero">
        <div>
          <div className="fraud-score-label">Document assurance rating</div>
          <div className="fraud-score-value">{fraudAnalysis?.riskScore ?? 0}<span>/100</span></div>
        </div>
        <div className={`fraud-severity-badge ${tone.badgeClass}`}>{tone.label}</div>
      </div>

      <div className="fraud-summary-grid">
        <div className="fraud-summary-stat">
          <div className="fraud-summary-label">Documents Reviewed</div>
          <div className="fraud-summary-value">{fraudAnalysis?.supportingDocsReviewed ?? 0}</div>
          <div className="fraud-summary-sub">{fraudAnalysis?.matchedDocuments ?? 0} matched cleanly</div>
        </div>
        <div className="fraud-summary-stat">
          <div className="fraud-summary-label">Verified Spend</div>
          <div className="fraud-summary-value">{formatCurrency(fraudAnalysis?.verifiedSpendAmount ?? 0)}</div>
          <div className="fraud-summary-sub">{fraudAnalysis?.verifiedSpendPct ?? 0}% coverage across reviewed vendors</div>
        </div>
        <div className="fraud-summary-stat">
          <div className="fraud-summary-label">Open Flags</div>
          <div className="fraud-summary-value">{flags.length}</div>
          <div className="fraud-summary-sub">{fraudAnalysis?.duplicateDocuments ?? 0} duplicate indicator(s)</div>
        </div>
      </div>

      <div className="report-callout">
        <div className="report-callout-label">Assurance Summary</div>
        {fraudAnalysis?.summary}
      </div>

      {anomalies.length > 0 && (
        <div className="fraud-report-block" id={buildSectionId(sectionIdPrefix, 'forensic')}>
          <div className="fraud-block-title">Forensic Transaction Analysis</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {anomalies.map((anomaly) => (
              <div key={anomaly.testName} style={{ padding: '12px 14px', background: 'var(--surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: anomaly.status === 'flag' ? (anomaly.severity === 'high' ? '#C0392B' : anomaly.severity === 'medium' ? '#E67E22' : '#2ECC71') : '#2ECC71' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{anomaly.testName}</span>
                  <span className={`fraud-severity-badge compact ${anomaly.status === 'flag' ? anomaly.severity : 'low'}`}>
                    {anomaly.status === 'flag' ? anomaly.severity : 'pass'}
                  </span>
                </div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {anomaly.detail}
                </div>
                {anomaly.testName === "Benford's Law" && anomaly.sampleSize && anomaly.sampleSize > 0 && (
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '6px' }}>
                    Sample size: {anomaly.sampleSize} transactions · χ² statistic: {anomaly.chiSquared?.toFixed(2) ?? 'N/A'}
                  </div>
                )}
                {anomaly.testName === 'Round-Number Bias' && (
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '6px' }}>
                    {anomaly.roundCount ?? 0} of {anomaly.totalCount ?? 0} transactions ({anomaly.roundPct ?? 0}%) are round numbers
                  </div>
                )}
                {anomaly.testName === 'Temporal Patterns' && (
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '6px' }}>
                    Weekend: {anomaly.weekendTxPct ?? 0}% · Same-day duplicates: {anomaly.sameDayDuplicates ?? 0} · Month-end: {anomaly.monthEndClusterPct ?? 0}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {flags.length > 0 ? (
        <div className="fraud-report-block" id={buildSectionId(sectionIdPrefix, 'flags')}>
          <div className="fraud-block-title">Flagged Findings</div>
          <div className="fraud-flag-list">
            {flags.map((flag) => (
              <div className="fraud-flag-item" key={`${flag.category}-${flag.title}-${flag.documentName ?? 'na'}`}>
                <div className={`fraud-flag-dot ${flag.severity}`} />
                <div style={{ flex: 1 }}>
                  <div className="fraud-flag-head">
                    <div className="fraud-flag-title">{flag.title}</div>
                    <div className={`fraud-severity-badge compact ${flag.severity}`}>{flag.severity}</div>
                  </div>
                  <div className="fraud-flag-detail">{flag.detail}</div>
                  <div className="fraud-flag-meta">
                    {flag.documentName ? `Document: ${flag.documentName}` : 'Document: n/a'}
                    {flag.vendor ? ` · Vendor: ${flag.vendor}` : ''}
                    {flag.transactionDate ? ` · Date: ${flag.transactionDate}` : ''}
                  </div>
                  <div className="fraud-flag-action">{flag.recommendedAction}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="fraud-report-block" id={buildSectionId(sectionIdPrefix, 'flags')}>
          <div className="fraud-block-title">Flagged Findings</div>
          <div className="fraud-empty-note">
            {hasDocuments
              ? 'No material anomalies were detected across the uploaded supporting documents for this run.'
              : 'No supporting documents were uploaded for this run. GreenLens still completed ledger-only anomaly checks on the transaction CSV.'}
          </div>
        </div>
      )}

      <div className="fraud-report-block" id={buildSectionId(sectionIdPrefix, 'documents')}>
        <div className="fraud-block-title">Documents Reviewed</div>
        {documents.length > 0 ? (
          <div className="fraud-doc-grid">
            {documents.map((document) => (
              <div className="fraud-doc-card" key={document.fileName}>
                <div className="fraud-doc-top">
                  <div>
                    <div className="fraud-doc-name">{document.fileName}</div>
                    <div className="fraud-doc-meta">
                      {(document.issuer || 'Unknown issuer')} · {document.documentType.replaceAll('_', ' ')}
                    </div>
                  </div>
                  <div className={`fraud-status-pill ${document.matchStatus}`}>{formatMatchStatus(document.matchStatus)}</div>
                </div>

                <div className="fraud-doc-stats">
                  <div>
                    <span>Total</span>
                    <strong>{document.totalAmount != null ? formatCurrency(document.totalAmount) : 'n/a'}</strong>
                  </div>
                  <div>
                    <span>Matched Amount</span>
                    <strong>{document.matchedAmount != null ? formatCurrency(document.matchedAmount) : 'n/a'}</strong>
                  </div>
                  <div>
                    <span>Delta</span>
                    <strong>{document.amountDelta != null ? formatCurrency(document.amountDelta) : 'n/a'}</strong>
                  </div>
                </div>

                <div className="fraud-doc-meta">
                  {document.referenceId ? `Ref ${document.referenceId}` : 'No extracted reference'}
                  {document.issueDate ? ` · ${document.issueDate}` : ''}
                </div>

                {document.parserNotes.length > 0 ? (
                  <div className="fraud-doc-note">{document.parserNotes.join(' ')}</div>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <div className="fraud-empty-note">
            No supporting documents were uploaded for this analysis, so GreenLens could not verify invoices, utility bills, or receipts.
          </div>
        )}
      </div>
    </div>
  );
}
