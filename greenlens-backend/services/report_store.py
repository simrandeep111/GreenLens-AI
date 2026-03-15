"""
Helpers for loading completed report payloads from memory or disk.
"""

from __future__ import annotations

import json

from core.config import PROCESSED_DIR
from core.job_store import get_job


def _normalize_report_result(report: dict) -> dict:
    normalized = dict(report)
    normalized.setdefault("reportId", "GL-LEGACY")
    normalized.setdefault("generatedAt", "")
    normalized.setdefault("reportSource", "unknown")

    company_defaults = {
        "name": "",
        "province": "",
        "industry": "",
        "employees": 0,
        "revenue": "",
    }
    score_defaults = {
        "total": 0,
        "environmental": 0,
        "social": 0,
        "governance": 0,
        "grade": "N/A",
    }
    emissions_defaults = {
        "totalTCO2e": 0.0,
        "scope1": 0.0,
        "scope2": 0.0,
        "scope3": 0.0,
        "intensityKgPerRevenue": 0.0,
        "breakdown": [],
    }
    benchmark_defaults = {
        "yourIntensity": 0.0,
        "sectorAverage": 0.0,
        "topQuartile": 0.0,
    }
    report_sections_defaults = {
        "executiveSummary": "",
        "emissionsNarrative": "",
        "complianceNarrative": "",
        "fraudNarrative": "Supporting document assurance was not available for this report.",
        "fundingNarrative": "",
        "actionsNarrative": "",
    }

    fraud_defaults = {
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
        "transactionAnomalies": [],
    }

    existing_company = normalized.get("company")
    normalized["company"] = {
        **company_defaults,
        **(existing_company if isinstance(existing_company, dict) else {}),
    }

    existing_score = normalized.get("score")
    normalized["score"] = {
        **score_defaults,
        **(existing_score if isinstance(existing_score, dict) else {}),
    }

    existing_emissions = normalized.get("emissions")
    if isinstance(existing_emissions, dict):
        normalized["emissions"] = {
            **emissions_defaults,
            **existing_emissions,
            "breakdown": existing_emissions.get("breakdown") or [],
            "benchmark": {
                **benchmark_defaults,
                **(existing_emissions.get("benchmark") or {}),
            },
        }
    else:
        normalized["emissions"] = {
            **emissions_defaults,
            "benchmark": benchmark_defaults,
        }

    existing_fraud = normalized.get("fraudAnalysis")
    if isinstance(existing_fraud, dict):
        for key, default_value in fraud_defaults.items():
            existing_fraud.setdefault(key, default_value)
        if not isinstance(existing_fraud.get("flags"), list):
            existing_fraud["flags"] = []
        if not isinstance(existing_fraud.get("documents"), list):
            existing_fraud["documents"] = []
        if not isinstance(existing_fraud.get("transactionAnomalies"), list):
            existing_fraud["transactionAnomalies"] = []
    else:
        normalized["fraudAnalysis"] = fraud_defaults

    existing_sections = normalized.get("reportSections")
    normalized["reportSections"] = {
        **report_sections_defaults,
        **(existing_sections if isinstance(existing_sections, dict) else {}),
    }
    normalized["compliance"] = normalized.get("compliance") if isinstance(normalized.get("compliance"), list) else []
    normalized["grants"] = normalized.get("grants") if isinstance(normalized.get("grants"), list) else []
    normalized["recommendations"] = normalized.get("recommendations") if isinstance(normalized.get("recommendations"), list) else []
    normalized.setdefault("totalGrantsAvailable", "$0")
    normalized.setdefault("complianceReadinessPct", 0)
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
