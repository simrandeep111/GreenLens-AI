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

export default function SupportingDocumentsSection({ fraudAnalysis }: { fraudAnalysis: FraudAnalysis }) {
  const tone = getRiskTone(fraudAnalysis.overallRisk);

  return (
    <div className="fraud-report-shell">
      <div className="fraud-report-hero">
        <div>
          <div className="fraud-score-label">Document assurance rating</div>
          <div className="fraud-score-value">{fraudAnalysis.riskScore}<span>/100</span></div>
        </div>
        <div className={`fraud-severity-badge ${tone.badgeClass}`}>{tone.label}</div>
      </div>

      <div className="fraud-summary-grid">
        <div className="fraud-summary-stat">
          <div className="fraud-summary-label">Documents Reviewed</div>
          <div className="fraud-summary-value">{fraudAnalysis.supportingDocsReviewed}</div>
          <div className="fraud-summary-sub">{fraudAnalysis.matchedDocuments} matched cleanly</div>
        </div>
        <div className="fraud-summary-stat">
          <div className="fraud-summary-label">Verified Spend</div>
          <div className="fraud-summary-value">{formatCurrency(fraudAnalysis.verifiedSpendAmount)}</div>
          <div className="fraud-summary-sub">{fraudAnalysis.verifiedSpendPct}% coverage across reviewed vendors</div>
        </div>
        <div className="fraud-summary-stat">
          <div className="fraud-summary-label">Open Flags</div>
          <div className="fraud-summary-value">{fraudAnalysis.flags.length}</div>
          <div className="fraud-summary-sub">{fraudAnalysis.duplicateDocuments} duplicate indicator(s)</div>
        </div>
      </div>

      <div className="report-callout">
        <div className="report-callout-label">Assurance Summary</div>
        {fraudAnalysis.summary}
      </div>

      {fraudAnalysis.flags.length > 0 ? (
        <div className="fraud-report-block">
          <div className="fraud-block-title">Flagged Findings</div>
          <div className="fraud-flag-list">
            {fraudAnalysis.flags.map((flag) => (
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
        <div className="fraud-report-block">
          <div className="fraud-block-title">Flagged Findings</div>
          <div className="fraud-empty-note">
            No material anomalies were detected across the uploaded supporting documents for this run.
          </div>
        </div>
      )}

      <div className="fraud-report-block">
        <div className="fraud-block-title">Documents Reviewed</div>
        {fraudAnalysis.documents.length > 0 ? (
          <div className="fraud-doc-grid">
            {fraudAnalysis.documents.map((document) => (
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
