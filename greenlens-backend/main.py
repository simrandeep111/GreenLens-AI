"""
GreenLens AI — FastAPI Backend
"""

from datetime import datetime, timezone
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import ALLOWED_ORIGINS
from api.upload import router as upload_router
from api.analyze import router as analyze_router
from api.status import router as status_router
from api.report import router as report_router
from api.report_chat import router as report_chat_router

app = FastAPI(
    title="GreenLens AI API",
    description="ESG intelligence backend for Canadian SMBs",
    version="0.1.0",
)

APP_BOOT_ID = str(uuid.uuid4())
APP_STARTED_AT = datetime.now(timezone.utc).isoformat()

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(upload_router,  prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(status_router,  prefix="/api")
app.include_router(report_router,  prefix="/api")
app.include_router(report_chat_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "GreenLens AI API",
        "status": "ok",
        "bootId": APP_BOOT_ID,
        "startedAt": APP_STARTED_AT,
    }
