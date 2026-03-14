"""
GET /api/report/{jobId} — returns the complete ESG report.
"""

from fastapi import APIRouter, HTTPException

from core.job_store import get_job
from services.report_store import load_report_result

router = APIRouter()


@router.get("/report/{job_id}")
async def get_report(job_id: str):
    report = load_report_result(job_id)
    if report is not None:
        return report

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] != "complete":
        raise HTTPException(
            status_code=202,
            detail=f"Job still {job['status']}. Poll /api/status/{job_id} to track progress.",
        )

    return job["result"]
