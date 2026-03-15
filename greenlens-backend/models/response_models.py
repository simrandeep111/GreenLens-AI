"""
Pydantic models for API responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    uploadId: str


class AnalyzeResponse(BaseModel):
    jobId: str


class StatusResponse(BaseModel):
    jobId: str
    status: str          # queued | running | complete | error
    currentStep: int     # 1-7
    stepLabel: str
    progress: int        # 0-100
    error: Optional[str] = None
    fraudAlert: Optional[dict] = None


class EmissionBreakdown(BaseModel):
    category: str
    scope: str
    tCO2e: float
    percentOfTotal: float


class Benchmark(BaseModel):
    yourIntensity: float
    sectorAverage: float
    topQuartile: float


class ScoreResponse(BaseModel):
    total: int
    environmental: int
    social: int
    governance: int
    grade: str


class ComplianceItem(BaseModel):
    framework: str
    status: str  # pass | warn | fail
    detail: str


class GrantItem(BaseModel):
    name: str
    amount: str
    description: str
    tags: list[str]


class RecommendationItem(BaseModel):
    text: str
    impactLabel: str


class SupportingDocumentReview(BaseModel):
    fileName: str
    documentType: str
    issuer: Optional[str] = None
    issueDate: Optional[str] = None
    referenceId: Optional[str] = None
    totalAmount: Optional[float] = None
    matchStatus: str
    matchedVendor: Optional[str] = None
    matchedDate: Optional[str] = None
    matchedAmount: Optional[float] = None
    amountDelta: Optional[float] = None
    parserNotes: list[str] = Field(default_factory=list)


class FraudFlag(BaseModel):
    severity: str
    category: str
    title: str
    detail: str
    documentName: Optional[str] = None
    vendor: Optional[str] = None
    transactionDate: Optional[str] = None
    documentAmount: Optional[float] = None
    matchedAmount: Optional[float] = None
    recommendedAction: str


class FraudAnalysisResponse(BaseModel):
    overallRisk: str
    riskScore: int
    summary: str
    supportingDocsReviewed: int
    matchedDocuments: int
    partialMatches: int
    unmatchedDocuments: int
    duplicateDocuments: int
    verifiedSpendAmount: float
    reviewedVendorSpendAmount: float
    verifiedSpendPct: int
    flags: list[FraudFlag]
    documents: list[SupportingDocumentReview]
    transactionAnomalies: list[dict] = Field(default_factory=list)


class ReportSections(BaseModel):
    executiveSummary: str
    emissionsNarrative: str
    complianceNarrative: str
    fraudNarrative: str
    fundingNarrative: str
    actionsNarrative: str


class CompanyResponse(BaseModel):
    name: str
    province: str
    industry: str
    employees: int
    revenue: str


class EmissionsResponse(BaseModel):
    totalTCO2e: float
    scope1: float
    scope2: float
    scope3: float
    intensityKgPerRevenue: float
    breakdown: list[EmissionBreakdown]
    benchmark: Benchmark


class ReportResponse(BaseModel):
    reportId: str
    generatedAt: str
    reportSource: str
    company: CompanyResponse
    score: ScoreResponse
    emissions: EmissionsResponse
    compliance: list[ComplianceItem]
    complianceReadinessPct: int
    fraudAnalysis: FraudAnalysisResponse
    grants: list[GrantItem]
    totalGrantsAvailable: str
    recommendations: list[RecommendationItem]
    reportSections: ReportSections


class ChatCitation(BaseModel):
    chunkId: str
    title: str
    sourceLabel: str
    excerpt: str
    sectionId: Optional[str] = None


class ReportChatResponse(BaseModel):
    answer: str
    answerSource: str
    citations: list[ChatCitation]
