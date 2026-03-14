"""
POST /api/upload — accepts CSV + optional PDF files, saves locally.
"""

import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from core.config import UPLOADS_DIR
from models.response_models import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    csv_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(default=[]),
):
    # Validate CSV
    if not csv_file.filename or not csv_file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A .csv file is required")

    upload_id = str(uuid.uuid4())
    upload_dir = UPLOADS_DIR / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_path = upload_dir / "input.csv"
    with open(csv_path, "wb") as f:
        shutil.copyfileobj(csv_file.file, f)

    # Save optional PDFs
    for i, pdf in enumerate(pdf_files):
        if pdf.filename:
            pdf_path = upload_dir / f"support_{i+1}.pdf"
            with open(pdf_path, "wb") as f:
                shutil.copyfileobj(pdf.file, f)

    return UploadResponse(uploadId=upload_id)
