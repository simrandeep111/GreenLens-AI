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
    normalized.setdefault(
        "fraudAnalysis",
        {
            "overallRisk": "not_assessed",
            "riskScore": 0,
            "summary": "No supporting documents were reviewed for this legacy report.",
            "supportingDocsReviewed": 0,
            "matchedDocuments": 0,
            "partialMatches": 0,
            "unmatchedDocuments": 0,
            "duplicateDocuments": 0,
            "verifiedSpendAmount": 0.0,
            "reviewedVendorSpendAmount": 0.0,
            "verifiedSpendPct": 0,
            "flags": [],
            "documents": [],
        },
    )
    if "reportSections" in normalized:
        normalized["reportSections"].setdefault(
            "fraudNarrative",
            "Supporting document assurance was not available for this legacy report.",
        )
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
