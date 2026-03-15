"""
Report generator — uses Moorcheh API to call Claude for narrative generation.
All numeric data is passed IN, the LLM only writes prose.
"""

from __future__ import annotations
import json

from services.moorcheh_client import call_moorcheh_answer

REQUIRED_REPORT_KEYS = [
    "executiveSummary",
    "emissionsNarrative",
    "complianceNarrative",
    "fraudNarrative",
    "fundingNarrative",
    "actionsNarrative",
]


def _summarize_transaction_anomalies(fraud_analysis: dict) -> str:
    anomalies = fraud_analysis.get("transactionAnomalies", [])
    if not anomalies:
        return "- No transaction-level anomaly tests were available."

    formatted = []
    for anomaly in anomalies[:3]:
        formatted.append(
            f"- {anomaly.get('testName', 'Unknown test')} [{anomaly.get('status', 'unknown')}/{anomaly.get('severity', 'info')}]: "
            f"{anomaly.get('detail', '')}"
        )
    return "\n".join(formatted)

def _build_report_prompt(
    company: dict,
    score: dict,
    emissions: dict,
    benchmark: dict,
    compliance_context: str,
    fraud_analysis: dict,
    grants_context: str,
    recommendations: list[dict],
) -> str:
    recs_text = "\n".join(
        f"- {r['text']} (Impact: {r['impactLabel']})" for r in recommendations
    )

    breakdown_text = "\n".join(
        f"  - {b['category']}: {b['tCO2e']} tCO2e ({b['scope']}, {b['percentOfTotal']}%)"
        for b in emissions.get("breakdown", [])
    )
    fraud_flags = fraud_analysis.get("flags", [])
    fraud_flags_text = "\n".join(
        f"- [{flag['severity'].upper()}] {flag['title']}: {flag['detail']}"
        for flag in fraud_flags[:5]
    ) or "- No material fraud flags detected."
    anomaly_text = _summarize_transaction_anomalies(fraud_analysis)

    return f"""You are an expert ESG analyst at a Canadian sustainability consulting firm.
Write a professional ESG report based on the following verified data. 

IMPORTANT: Return ONLY a valid JSON object with exactly these 6 keys:
- executiveSummary
- emissionsNarrative
- complianceNarrative
- fraudNarrative
- fundingNarrative
- actionsNarrative

Each value should be a string of 1-2 compact paragraphs of professional prose.

--- COMPANY DATA ---
Name: {company['name']}
Province: {company['province']}
Industry: {company['industry']}
Employees: {company['employees']}
Revenue: {company['revenue']}

--- ESG SCORE (deterministically calculated, do NOT change these) ---
Total: {score['total']}/100
Environmental: {score['environmental']}/50
Social: {score['social']}/25
Governance: {score['governance']}/25
Grade: {score['grade']}

--- EMISSIONS DATA (verified calculations) ---
Total: {emissions['totalTCO2e']} tCO2e
Scope 1 (direct): {emissions['scope1']} tCO2e
Scope 2 (energy): {emissions['scope2']} tCO2e
Scope 3 (value chain): {emissions['scope3']} tCO2e
Emission intensity: {benchmark['yourIntensity']} kgCO2e per $1,000 revenue
Sector average: {benchmark['sectorAverage']} kgCO2e per $1,000 revenue

Breakdown:
{breakdown_text}

--- REGULATORY CONTEXT ---
{compliance_context}

--- SUPPORTING DOCUMENT ASSURANCE / FRAUD SIGNALS ---
Overall risk: {fraud_analysis['overallRisk']}
Risk score: {fraud_analysis['riskScore']}/100
Summary: {fraud_analysis['summary']}
Supporting docs reviewed: {fraud_analysis['supportingDocsReviewed']}
Matched documents: {fraud_analysis['matchedDocuments']}
Partial matches: {fraud_analysis['partialMatches']}
Unmatched documents: {fraud_analysis['unmatchedDocuments']}
Duplicate documents: {fraud_analysis['duplicateDocuments']}
Verified spend amount: ${fraud_analysis['verifiedSpendAmount']:.2f}
Verified spend coverage across reviewed vendors: {fraud_analysis['verifiedSpendPct']}%

Top document assurance findings:
{fraud_flags_text}

Forensic ledger tests:
{anomaly_text}

--- AVAILABLE GRANTS ---
{grants_context}

--- PRIORITY RECOMMENDATIONS ---
{recs_text}

RULES:
1. Use Canadian regulatory language. Cite specific frameworks (OSFI B-15, GHG Protocol, GRI, CBCA).
2. Be specific — cite the exact numbers provided above.
3. Do NOT invent or change any scores, emission data, or grant amounts.
4. Write in third person (e.g., "{company['name']} has achieved...").
5. Return ONLY the JSON object, no markdown fences, no explanation outside it.
6. Escape any double quotes that appear inside string values.
7. If you want paragraph breaks, encode them as \\n\\n inside the JSON string values.
8. Do not use bullet lists inside string values.
"""


def _build_fallback_report(
    company: dict,
    score: dict,
    emissions: dict,
    benchmark: dict,
    fraud_analysis: dict,
    recommendations: list[dict],
) -> dict:
    """Fallback report if the LLM call fails — uses template text."""
    name = company["name"]
    grade = score["grade"]
    total = score["total"]
    e_score = score["environmental"]
    s_score = score["social"]
    g_score = score["governance"]
    total_e = emissions["totalTCO2e"]
    s1 = emissions["scope1"]
    s2 = emissions["scope2"]
    s3 = emissions["scope3"]
    intensity = benchmark["yourIntensity"]
    avg = benchmark["sectorAverage"]
    docs_reviewed = int(fraud_analysis.get("supportingDocsReviewed", 0) or 0)
    fraud_summary = str(fraud_analysis.get("summary", "")).strip()
    flagged_anomalies = [
        anomaly for anomaly in fraud_analysis.get("transactionAnomalies", [])
        if anomaly.get("status") == "flag"
    ]
    flagged_names = ", ".join(anomaly.get("testName", "unknown test") for anomaly in flagged_anomalies[:3])

    if docs_reviewed > 0:
        fraud_intro = (
            f"GreenLens reviewed {docs_reviewed} uploaded supporting document(s) and cross-checked them against the ledger "
            f"for duplicate references, amount mismatches, and missing evidence coverage."
        )
    else:
        fraud_intro = (
            "No supporting documents were uploaded for this run, so GreenLens performed ledger-only forensic testing "
            "on the transaction CSV using Benford, round-number, and temporal-pattern checks."
        )

    if flagged_anomalies:
        anomaly_note = (
            f" Transaction-level tests flagged {len(flagged_anomalies)} area(s), including {flagged_names}. "
            f"These patterns should be reviewed before relying on the records for external assurance."
        )
    else:
        anomaly_note = (
            " Transaction-level forensic checks did not surface material anomalies in amount distribution or timing."
        )

    return {
        "executiveSummary": (
            f"{name} achieved an overall ESG score of {total} out of 100 for fiscal year 2024, "
            f"placing the company in the {grade} tier as defined by the GreenLens ESG assessment framework. "
            f"The Environmental sub-score of {e_score}/50 reflects the company's emission intensity of "
            f"{intensity} kgCO2e per $1,000 of revenue against a sector average of {avg} kgCO2e. "
            f"The Social sub-score of {s_score}/25 and Governance sub-score of {g_score}/25 reflect "
            f"self-reported policy and disclosure maturity."
        ),
        "emissionsNarrative": (
            f"Total verified greenhouse gas emissions for the reporting period were {total_e} tCO2e. "
            f"Scope 1 (direct) emissions of {s1} tCO2e include natural gas heating and fleet vehicle fuel. "
            f"Scope 2 (energy) emissions of {s2} tCO2e reflect grid electricity consumption. "
            f"Scope 3 (value chain) emissions of {s3} tCO2e include supply chain, waste, and business travel."
        ),
        "complianceNarrative": (
            f"{name} meets GHG Protocol reporting requirements. OSFI Guideline B-15 compliance "
            f"has gaps that are addressable within one fiscal year. Full CBCA annual sustainability "
            f"disclosure has not yet been published."
        ),
        "fraudNarrative": (
            f"{fraud_intro} {fraud_summary}{anomaly_note}"
        ),
        "fundingNarrative": (
            f"Based on {name}'s province, industry, and size, GreenLens has identified eligible "
            f"government programs. These include commercial energy efficiency grants, fleet electrification "
            f"incentives, and clean technology tax credits."
        ),
        "actionsNarrative": (
            f"Priority actions include fleet transition, formal sustainability disclosure, "
            f"climate transition planning, supplier engagement for Scope 3, and facility upgrades."
        ),
    }


def _clean_llm_json(raw: str) -> str:
    """Strip code fences and isolate the outer JSON object."""
    cleaned = raw.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]

    cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    return (
        cleaned
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .strip()
    )


def _validate_report_payload(report: dict) -> dict:
    missing = [key for key in REQUIRED_REPORT_KEYS if key not in report]
    if missing:
        raise ValueError(f"Missing keys: {missing}")

    return {
        key: str(report[key]).strip()
        for key in REQUIRED_REPORT_KEYS
    }


def _normalize_extracted_value(value: str) -> str:
    return (
        value.strip()
        .rstrip(",")
        .strip()
        .removeprefix('"')
        .removesuffix('"')
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\\\", "\\")
        .strip()
    )


def _extract_report_fields_manually(cleaned: str) -> dict | None:
    """
    Recover a near-JSON response by slicing between known field names.
    This helps when the model forgets to escape a quote or newline.
    """
    positions: dict[str, int] = {}
    for key in REQUIRED_REPORT_KEYS:
        marker = f'"{key}"'
        idx = cleaned.find(marker)
        if idx == -1:
            return None
        positions[key] = idx

    ordered_keys = sorted(REQUIRED_REPORT_KEYS, key=lambda key: positions[key])
    extracted: dict[str, str] = {}

    for idx, key in enumerate(ordered_keys):
        marker = f'"{key}"'
        colon_idx = cleaned.find(":", positions[key] + len(marker))
        if colon_idx == -1:
            return None

        value_start = colon_idx + 1
        while value_start < len(cleaned) and cleaned[value_start].isspace():
            value_start += 1

        if idx + 1 < len(ordered_keys):
            next_marker = f'"{ordered_keys[idx + 1]}"'
            next_idx = cleaned.find(next_marker, value_start)
            if next_idx == -1:
                return None
            chunk = cleaned[value_start:next_idx]
        else:
            next_idx = cleaned.rfind("}")
            if next_idx == -1:
                return None
            chunk = cleaned[value_start:next_idx]

        extracted[key] = _normalize_extracted_value(chunk)

    return extracted


def _parse_report_json(raw: str) -> dict:
    cleaned = _clean_llm_json(raw)

    try:
        return _validate_report_payload(json.loads(cleaned, strict=False))
    except (json.JSONDecodeError, ValueError) as primary_error:
        recovered = _extract_report_fields_manually(cleaned)
        if recovered is None:
            raise primary_error

        print("[REPORT] Recovered malformed LLM JSON with manual field extraction")
        return _validate_report_payload(recovered)


def generate_report(
    company: dict,
    score: dict,
    emissions: dict,
    benchmark: dict,
    compliance_context: str,
    fraud_analysis: dict,
    grants_context: str,
    recommendations: list[dict],
) -> dict:
    """
    Generate the report narrative using the LLM, with fallback if it fails.
    Returns a tuple of (report_sections, source).
    """
    prompt = _build_report_prompt(
        company, score, emissions, benchmark,
        compliance_context, fraud_analysis, grants_context, recommendations,
    )

    raw = call_moorcheh_answer(prompt, temperature=0.3, timeout=180.0)

    if not raw:
        print("[REPORT] LLM returned empty — using fallback template")
        return _build_fallback_report(company, score, emissions, benchmark, fraud_analysis, recommendations), "fallback"

    # Try to parse JSON from the response
    try:
        report = _parse_report_json(raw)
        print("[REPORT] Parsed LLM response successfully")
        return report, "llm"

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[REPORT] Failed to parse LLM JSON: {e}")
        print(f"[REPORT] Raw response: {raw[:500]}")
        return _build_fallback_report(company, score, emissions, benchmark, fraud_analysis, recommendations), "fallback"
