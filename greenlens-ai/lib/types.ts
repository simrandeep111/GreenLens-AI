// Company intake data
export interface CompanyData {
  name: string;
  province: string;
  industry: string;
  employees: number;
  revenue: string;
}

// ESG scoring
export interface ESGScore {
  total: number;
  environmental: number;
  social: number;
  governance: number;
  grade: string;
}

// Emissions breakdown
export interface EmissionEntry {
  category: string;
  scope: 'Scope 1' | 'Scope 2' | 'Scope 3' | string;
  tCO2e: number;
  percentOfTotal: number;
}

// Government grants
export interface Grant {
  name: string;
  amount: string;
  description: string;
  tags: string[];
}

// Dashboard recommendations
export interface Recommendation {
  text: string;
  impactLabel: string;
}

export interface SupportingDocumentReview {
  fileName: string;
  documentType: string;
  issuer?: string | null;
  issueDate?: string | null;
  referenceId?: string | null;
  totalAmount?: number | null;
  matchStatus: 'matched' | 'partial' | 'unmatched' | string;
  matchedVendor?: string | null;
  matchedDate?: string | null;
  matchedAmount?: number | null;
  amountDelta?: number | null;
  parserNotes: string[];
}

export interface FraudFlag {
  severity: 'high' | 'medium' | 'low' | string;
  category: string;
  title: string;
  detail: string;
  documentName?: string | null;
  vendor?: string | null;
  transactionDate?: string | null;
  documentAmount?: number | null;
  matchedAmount?: number | null;
  recommendedAction: string;
}

export interface FraudAnalysis {
  overallRisk: 'high' | 'medium' | 'low' | 'not_assessed' | string;
  riskScore: number;
  summary: string;
  supportingDocsReviewed: number;
  matchedDocuments: number;
  partialMatches: number;
  unmatchedDocuments: number;
  duplicateDocuments: number;
  verifiedSpendAmount: number;
  reviewedVendorSpendAmount: number;
  verifiedSpendPct: number;
  flags: FraudFlag[];
  documents: SupportingDocumentReview[];
}

// Compliance items
export interface ComplianceItem {
  framework: string;
  status: 'pass' | 'warn' | 'fail';
  detail: string;
}

// Processing steps
export interface ProcessingStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'done';
}

export interface BenchmarkData {
  yourIntensity: number;
  sectorAverage: number;
  topQuartile: number;
}

export interface EmissionsData {
  totalTCO2e: number;
  scope1: number;
  scope2: number;
  scope3: number;
  intensityKgPerRevenue: number;
  breakdown: EmissionEntry[];
  benchmark: BenchmarkData;
}

export interface ReportSections {
  executiveSummary: string;
  emissionsNarrative: string;
  complianceNarrative: string;
  fraudNarrative: string;
  fundingNarrative: string;
  actionsNarrative: string;
}

export interface ReportChatCitation {
  chunkId: string;
  title: string;
  sourceLabel: string;
  excerpt: string;
  sectionId?: string | null;
}

export interface ReportChatResponse {
  answer: string;
  answerSource: 'llm' | 'fallback' | string;
  citations: ReportChatCitation[];
}

export interface ReportChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: ReportChatCitation[];
  answerSource?: 'llm' | 'fallback' | string;
}

export interface ReportResponse {
  reportId: string;
  generatedAt: string;
  reportSource: 'llm' | 'fallback' | string;
  company: CompanyData;
  score: ESGScore;
  emissions: EmissionsData;
  compliance: ComplianceItem[];
  complianceReadinessPct: number;
  fraudAnalysis: FraudAnalysis;
  grants: Grant[];
  totalGrantsAvailable: string;
  recommendations: Recommendation[];
  reportSections: ReportSections;
}

export interface BackendMeta {
  service: string;
  status: string;
  bootId: string;
  startedAt: string;
}

export interface JobStatus {
  jobId: string;
  status: 'queued' | 'running' | 'complete' | 'error' | 'failed';
  currentStep: number;
  stepLabel: string;
  progress: number;
  error?: string | null;
}

export interface AnalysisSession {
  company: CompanyData;
  governanceAnswers: string[];
  csvFileName: string | null;
  pdfFileNames: string[];
  uploadId: string | null;
  jobId: string | null;
  status: JobStatus | null;
  report: ReportResponse | null;
  backendBootId: string | null;
}
