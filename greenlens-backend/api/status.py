"""
GET /api/status/{jobId} — returns current pipeline progress.
"""

from fastapi import APIRouter, HTTPException

from core.job_store import get_job
from models.response_models import StatusResponse

router = APIRouter()


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return StatusResponse(
        jobId=job["job_id"],
        status=job["status"],
        currentStep=job["current_step"],
        stepLabel=job["step_label"],
        progress=job["progress"],
        error=job.get("error"),
    )
