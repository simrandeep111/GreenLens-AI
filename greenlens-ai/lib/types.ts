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
