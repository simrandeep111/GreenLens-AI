"""
Pydantic models for API requests.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CompanyInfo(BaseModel):
    name: str = Field(min_length=1)
    province: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    employees: int = Field(gt=0)
    revenue: str = Field(min_length=1)  # e.g. "$2,400,000"


class AnalyzeRequest(BaseModel):
    uploadId: str
    company: CompanyInfo
    governance_answers: list[str]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ReportChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)
