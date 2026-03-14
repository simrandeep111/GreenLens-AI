"""
POST /api/analyze — triggers background ESG pipeline.
"""

import uuid
import threading

from fastapi import APIRouter, HTTPException

from core.config import UPLOADS_DIR
from core.job_store import create_job, get_job
from models.request_models import AnalyzeRequest
from models.response_models import AnalyzeResponse
from services.pipeline import run_pipeline

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    # Verify upload exists
    upload_dir = UPLOADS_DIR / req.uploadId
    csv_path = upload_dir / "input.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"Upload {req.uploadId} not found")

    job_id = str(uuid.uuid4())

    # Create job entry
    create_job(
        job_id=job_id,
        upload_id=req.uploadId,
        company=req.company.model_dump(),
        governance_answers=req.governance_answers,
    )

    # Launch pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id,),
        daemon=True,
    )
    thread.start()

    return AnalyzeResponse(jobId=job_id)
