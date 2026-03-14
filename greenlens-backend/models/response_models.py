"""
Pydantic models for API responses.
"""

from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    uploadId: str


class AnalyzeResponse(BaseModel):
    jobId: str


class StatusResponse(BaseModel):
    jobId: str
    status: str          # queued | running | complete | error
    currentStep: int     # 1-6
    stepLabel: str
    progress: int        # 0-100
    error: Optional[str] = None


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


class ReportSections(BaseModel):
    executiveSummary: str
    emissionsNarrative: str
    complianceNarrative: str
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
