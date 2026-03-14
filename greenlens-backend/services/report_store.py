"""
Helpers for loading completed report payloads from memory or disk.
"""

from __future__ import annotations

import json

from core.config import PROCESSED_DIR
from core.job_store import get_job


def _normalize_report_result(report: dict) -> dict:
    normalized = dict(report)
    normalized.setdefault("reportSource", "unknown")
    return normalized


def load_report_result(job_id: str) -> dict | None:
    job = get_job(job_id)
    if job and job.get("result"):
        return _normalize_report_result(job["result"])

    report_path = PROCESSED_DIR / job_id / "final_report.json"
    if not report_path.exists():
        return None

    with open(report_path) as handle:
        return _normalize_report_result(json.load(handle))
