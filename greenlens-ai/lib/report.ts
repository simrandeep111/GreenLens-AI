import {
  BenchmarkData,
  ComplianceItem,
  EmissionsData,
  FraudAnalysis,
  FraudFlag,
  ReportResponse,
  ReportSections,
  SupportingDocumentReview,
  TransactionAnomaly,
} from '@/lib/types';

export const EMPTY_COMPANY = {
  name: '',
  province: '',
  industry: '',
  employees: 0,
  revenue: '',
};

export const EMPTY_SCORE = {
  total: 0,
  environmental: 0,
  social: 0,
  governance: 0,
  grade: 'N/A',
};

export const EMPTY_BENCHMARK: BenchmarkData = {
  yourIntensity: 0,
  sectorAverage: 0,
  topQuartile: 0,
};

export const EMPTY_EMISSIONS = {
  totalTCO2e: 0,
  scope1: 0,
  scope2: 0,
  scope3: 0,
  intensityKgPerRevenue: 0,
  breakdown: [],
  benchmark: EMPTY_BENCHMARK,
};

export const EMPTY_FRAUD_ANALYSIS: FraudAnalysis = {
  overallRisk: 'not_assessed',
  riskScore: 0,
  summary: 'No supporting documents were reviewed for this analysis.',
  supportingDocsReviewed: 0,
  matchedDocuments: 0,
  partialMatches: 0,
  unmatchedDocuments: 0,
  duplicateDocuments: 0,
  verifiedSpendAmount: 0,
  reviewedVendorSpendAmount: 0,
  verifiedSpendPct: 0,
  flags: [],
  documents: [],
  transactionAnomalies: [],
};

export const EMPTY_REPORT_SECTIONS: ReportSections = {
  executiveSummary: '',
  emissionsNarrative: '',
  complianceNarrative: '',
  fraudNarrative: '',
  fundingNarrative: '',
  actionsNarrative: '',
};

function normalizeFlag(flag: Partial<FraudFlag> | null | undefined): FraudFlag {
  return {
    severity: flag?.severity ?? 'low',
    category: flag?.category ?? 'general',
    title: flag?.title ?? 'Flagged item',
    detail: flag?.detail ?? '',
    documentName: flag?.documentName ?? null,
    vendor: flag?.vendor ?? null,
    transactionDate: flag?.transactionDate ?? null,
    documentAmount: flag?.documentAmount ?? null,
    matchedAmount: flag?.matchedAmount ?? null,
    recommendedAction: flag?.recommendedAction ?? 'Review the underlying records manually.',
  };
}

function normalizeDocument(
  document: Partial<SupportingDocumentReview> | null | undefined,
  index: number,
): SupportingDocumentReview {
  return {
    fileName: document?.fileName ?? `document-${index + 1}`,
    documentType: document?.documentType ?? 'unknown',
    issuer: document?.issuer ?? null,
    issueDate: document?.issueDate ?? null,
    referenceId: document?.referenceId ?? null,
    totalAmount: document?.totalAmount ?? null,
    matchStatus: document?.matchStatus ?? 'unmatched',
    matchedVendor: document?.matchedVendor ?? null,
    matchedDate: document?.matchedDate ?? null,
    matchedAmount: document?.matchedAmount ?? null,
    amountDelta: document?.amountDelta ?? null,
    parserNotes: document?.parserNotes ?? [],
  };
}

function normalizeAnomaly(
  anomaly: Partial<TransactionAnomaly> | null | undefined,
  index: number,
): TransactionAnomaly {
  return {
    testName: anomaly?.testName ?? `Anomaly Test ${index + 1}`,
    status: anomaly?.status ?? 'insufficient_data',
    severity: anomaly?.severity ?? 'info',
    detail: anomaly?.detail ?? '',
    observed: anomaly?.observed,
    expected: anomaly?.expected,
    chiSquared: anomaly?.chiSquared,
    sampleSize: anomaly?.sampleSize,
    roundPct: anomaly?.roundPct,
    roundCount: anomaly?.roundCount,
    totalCount: anomaly?.totalCount,
    weekendTxCount: anomaly?.weekendTxCount,
    weekendTxPct: anomaly?.weekendTxPct,
    sameDayDuplicates: anomaly?.sameDayDuplicates,
    monthEndClusterPct: anomaly?.monthEndClusterPct,
    findings: anomaly?.findings,
  };
}

export function normalizeFraudAnalysis(
  fraudAnalysis: Partial<FraudAnalysis> | null | undefined,
): FraudAnalysis {
  const value = fraudAnalysis ?? {};

  return {
    ...EMPTY_FRAUD_ANALYSIS,
    ...value,
    flags: (value.flags ?? []).map(normalizeFlag),
    documents: (value.documents ?? []).map(normalizeDocument),
    transactionAnomalies: (value.transactionAnomalies ?? []).map(normalizeAnomaly),
  };
}

function normalizeComplianceItem(item: Partial<ComplianceItem> | null | undefined): ComplianceItem {
  return {
    framework: item?.framework ?? 'Unknown framework',
    status: item?.status ?? 'warn',
    detail: item?.detail ?? '',
  };
}

export function normalizeReport(
  report: Partial<ReportResponse> | null | undefined,
): ReportResponse | null {
  if (!report) {
    return null;
  }

  const emissions: Partial<EmissionsData> = report.emissions ?? {};

  return {
    reportId: report.reportId ?? 'GL-DEMO',
    generatedAt: report.generatedAt ?? '',
    reportSource: report.reportSource ?? 'unknown',
    company: {
      ...EMPTY_COMPANY,
      ...(report.company ?? {}),
    },
    score: {
      ...EMPTY_SCORE,
      ...(report.score ?? {}),
    },
    emissions: {
      ...EMPTY_EMISSIONS,
      ...emissions,
      breakdown: emissions.breakdown ?? [],
      benchmark: {
        ...EMPTY_BENCHMARK,
        ...(emissions.benchmark ?? {}),
      },
    },
    compliance: (report.compliance ?? []).map(normalizeComplianceItem),
    complianceReadinessPct: report.complianceReadinessPct ?? 0,
    fraudAnalysis: normalizeFraudAnalysis(report.fraudAnalysis),
    grants: report.grants ?? [],
    totalGrantsAvailable: report.totalGrantsAvailable ?? '$0',
    recommendations: report.recommendations ?? [],
    reportSections: {
      ...EMPTY_REPORT_SECTIONS,
      ...(report.reportSections ?? {}),
    },
  };
}
