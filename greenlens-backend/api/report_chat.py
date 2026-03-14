"""
POST /api/report-chat/{jobId} — grounded report Q&A over the saved report plus ESG knowledge.
"""

from fastapi import APIRouter, HTTPException

from models.request_models import ReportChatRequest
from models.response_models import ReportChatResponse
from services.report_chat_service import answer_report_question
from services.report_store import load_report_result

router = APIRouter()


@router.post("/report-chat/{job_id}", response_model=ReportChatResponse)
async def report_chat(job_id: str, req: ReportChatRequest):
    report = load_report_result(job_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {job_id} not found")

    payload = answer_report_question(
        report=report,
        question=req.question,
        history=[item.model_dump() for item in req.history],
    )
    return ReportChatResponse(**payload)
