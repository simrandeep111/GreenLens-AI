"""
Pipeline orchestrator — runs the full ESG analysis end-to-end.
Updates job status at each step so the frontend processing screen can poll it.
"""

from __future__ import annotations
import time
import json
import traceback
from datetime import datetime, timezone

from core.config import UPLOADS_DIR, PROCESSED_DIR
from core.job_store import get_job, update_step, complete_job, fail_job

from services.csv_parser import parse_csv
from services.normalizer import normalize
from services.scope_classifier import classify_dataframe
from services.emissions_calculator import calculate_emissions, aggregate_emissions
from services.scoring_engine import calculate_full_score
from services.retrieval_service import (
    retrieve_compliance, retrieve_grants,
    format_compliance_context, format_grants_context,
)
from services.report_generator import generate_report


def _generate_recommendations(emissions: dict, score: dict, company: dict) -> list[dict]:
    """Deterministic recommendation rules based on computed data."""
    recs = []
    total = emissions["totalTCO2e"]
    s1 = emissions["scope1"]
    s3 = emissions["scope3"]

    # Rule 1: high Scope 1 from fuel → fleet electrification
    if s1 > 0 and (s1 / total) > 0.15:
        recs.append({
            "text": "Transition delivery fleet to plug-in hybrid or battery electric vehicles",
            "impactLabel": "+8 pts Environmental score",
        })

    # Rule 2: low governance score → publish disclosure
    if score["governance"] < 15:
        recs.append({
            "text": "Publish CBCA-compliant annual sustainability disclosure",
            "impactLabel": "+5 pts Governance score",
        })

    # Rule 3: OSFI gap → transition plan
    recs.append({
        "text": "Develop OSFI B-15 aligned climate transition plan",
        "impactLabel": "+4 pts Environmental score",
    })

    # Rule 4: high Scope 3 → supplier engagement
    if s3 > 0 and (s3 / total) > 0.40:
        recs.append({
            "text": "Launch supplier emissions data programme for top 5 vendors",
            "impactLabel": "+4 pts Environmental score",
        })

    # Rule 5: HVAC upgrade
    if s1 > 20:
        recs.append({
            "text": "Upgrade commercial HVAC to high-efficiency heat pump systems",
            "impactLabel": "+3 pts Environmental score",
        })

    return recs[:5]  # max 5 recommendations


def _generate_compliance(score: dict) -> list[dict]:
    """Deterministic compliance assessment."""
    items = [
        {
            "framework": "GHG Protocol",
            "status": "pass",
            "detail": "Full Scope 1, 2, and 3 emissions reporting completed. Methodology documented and emission factors appropriately sourced from NRCan.",
        },
        {
            "framework": "OSFI Guideline B-15",
            "status": "warn",
            "detail": "Gaps identified: (1) No formal climate transition plan published. (2) Physical climate risk assessment not conducted. (3) TCFD-aligned scenario analysis absent.",
        },
        {
            "framework": "GRI Standards",
            "status": "pass" if score["social"] >= 15 else "warn",
            "detail": "Material topic disclosures meet minimum threshold. Social and governance indicators reported through self-assessment.",
        },
        {
            "framework": "CBCA ESG Amendment",
            "status": "fail" if score["governance"] < 15 else "warn",
            "detail": "Annual sustainability disclosure has not been published. Under 2024 CBCA amendments, incorporated entities with >20 employees must disclose material ESG information.",
        },
    ]
    return items


def _generate_grants(grant_docs: list[dict]) -> tuple[list[dict], str]:
    """Convert retrieved grant documents into frontend grant items."""
    grants = []
    total = 0

    for doc in grant_docs:
        meta = doc.get("metadata", {})
        amount_str = meta.get("amount", "$0")
        amount_num = int(amount_str.replace("$", "").replace(",", "").strip() or "0")
        total += amount_num

        grants.append({
            "name": meta.get("program_name", "Unknown Program"),
            "amount": amount_str,
            "description": doc.get("content", "")[:200],
            "tags": meta.get("tags", []),
        })

    return grants, f"${total:,}"


def run_pipeline(job_id: str) -> None:
    """
    Main pipeline — runs in a background thread.
    Updates job_store at each step so the frontend can poll progress.
    """
    try:
        job = get_job(job_id)
        if not job:
            return

        company = job["company"]
        governance_answers = job["governance_answers"]
        upload_id = job["upload_id"]
        csv_path = UPLOADS_DIR / upload_id / "input.csv"

        # ── Step 1: Parse ──
        update_step(job_id, 1, "Parsing uploaded data", 10)
        time.sleep(0.8)  # simulate processing time
        df = parse_csv(csv_path)

        # ── Step 2: Normalize ──
        update_step(job_id, 2, "Normalizing merchants and categories", 25)
        time.sleep(0.6)
        df = normalize(df)

        # ── Step 3: Classify ──
        update_step(job_id, 3, "Classifying Scope 1 / 2 / 3", 40)
        time.sleep(0.8)
        df = classify_dataframe(df)

        # ── Step 4: Calculate emissions ──
        update_step(job_id, 4, "Calculating emissions and benchmarks", 55)
        time.sleep(0.6)
        df = calculate_emissions(df, company["province"])
        emissions = aggregate_emissions(df)

        # ── Step 4b: Score ──
        score_result = calculate_full_score(
            total_tCO2e=emissions["totalTCO2e"],
            revenue_str=company["revenue"],
            industry=company["industry"],
            governance_answers=governance_answers,
        )
        score = score_result["score"]
        benchmark = score_result["benchmark"]

        # Add intensity to emissions
        emissions["intensityKgPerRevenue"] = benchmark["yourIntensity"]

        # ── Step 5: Retrieve context ──
        update_step(job_id, 5, "Retrieving compliance and grant context", 70)
        time.sleep(0.5)

        compliance_docs = retrieve_compliance(company["province"], company["industry"])
        grant_docs = retrieve_grants(company["province"], company["industry"], company["employees"])

        compliance_context = format_compliance_context(compliance_docs)
        grants_context = format_grants_context(grant_docs)

        # Deterministic outputs
        compliance_items = _generate_compliance(score)
        grants, total_grants = _generate_grants(grant_docs)
        recommendations = _generate_recommendations(emissions, score, company)

        compliance_pass = sum(1 for c in compliance_items if c["status"] == "pass")
        compliance_pct = int((compliance_pass / len(compliance_items)) * 100) if compliance_items else 0

        # ── Step 6: Generate report narrative ──
        update_step(job_id, 6, "Generating ESG report", 85)
        report_sections, report_source = generate_report(
            company=company,
            score=score,
            emissions=emissions,
            benchmark=benchmark,
            compliance_context=compliance_context,
            grants_context=grants_context,
            recommendations=recommendations,
        )

        # Add benchmark to emissions for frontend
        emissions["benchmark"] = benchmark

        # ── Build final result ──
        result = {
            "reportId": f"GL-2024-{job_id[:5].upper()}",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "reportSource": report_source,
            "company": company,
            "score": score,
            "emissions": emissions,
            "compliance": compliance_items,
            "complianceReadinessPct": compliance_pct,
            "grants": grants,
            "totalGrantsAvailable": total_grants,
            "recommendations": recommendations,
            "reportSections": report_sections,
        }

        # Save to disk
        out_dir = PROCESSED_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "final_report.json", "w") as f:
            json.dump(result, f, indent=2)

        # ── Done ──
        complete_job(job_id, result)

    except Exception as e:
        traceback.print_exc()
        fail_job(job_id, str(e))
