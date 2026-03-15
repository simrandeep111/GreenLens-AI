"""
Supporting document assurance and fraud-signal detection.
Cross-checks uploaded bills, receipts, and invoices against ledger transactions.
Includes forensic accounting techniques: Benford's Law, round-number bias,
and temporal anomaly detection on the transaction ledger.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

import pandas as pd

from services.supporting_document_service import _canonicalize_vendor

SEVERITY_WEIGHTS = {
    "high": 18,
    "medium": 10,
    "low": 4,
}

# ── Benford's Law expected distribution of leading digits ──────────────
BENFORD_EXPECTED = {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def _flag(
    severity: str,
    category: str,
    title: str,
    detail: str,
    *,
    document_name: str | None = None,
    vendor: str | None = None,
    transaction_date: str | None = None,
    document_amount: float | None = None,
    matched_amount: float | None = None,
    recommended_action: str,
) -> dict:
    return {
        "severity": severity,
        "category": category,
        "title": title,
        "detail": detail,
        "documentName": document_name,
        "vendor": vendor,
        "transactionDate": transaction_date,
        "documentAmount": document_amount,
        "matchedAmount": matched_amount,
        "recommendedAction": recommended_action,
    }


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["txIndex"] = range(1, len(working) + 1)
    working["txDate"] = pd.to_datetime(working["date"], errors="coerce")
    working["matchVendor"] = working["canonical_vendor"].fillna(working["norm_vendor"].str.replace(" ", "_"))
    return working


def _candidate_rows(df: pd.DataFrame, document: dict) -> pd.DataFrame:
    vendor = document.get("canonicalVendor")
    if vendor:
        exact = df[df["matchVendor"] == vendor]
        if not exact.empty:
            return exact

    issuer = document.get("issuer") or ""
    issuer_tokens = {token for token in issuer.lower().replace("-", " ").split() if len(token) > 2}
    if not issuer_tokens:
        return df.iloc[0:0]

    return df[
        df["norm_vendor"].apply(
            lambda value: bool(issuer_tokens & {token for token in str(value).split() if len(token) > 2})
        )
    ]


def _score_candidate(row: pd.Series, document: dict) -> tuple[float, float | None, int | None]:
    score = 0.0
    vendor = document.get("canonicalVendor")
    if vendor and row["matchVendor"] == vendor:
        score += 40

    document_date = pd.to_datetime(document.get("issueDate"), errors="coerce")
    date_delta_days: int | None = None
    if pd.notna(document_date) and pd.notna(row["txDate"]):
        date_delta_days = abs((row["txDate"] - document_date).days)
        if date_delta_days <= 5:
            score += 25
        elif date_delta_days <= 15:
            score += 18
        elif date_delta_days <= 40:
            score += 8

    document_amount = document.get("totalAmount")
    amount_ratio: float | None = None
    if document_amount:
        amount_delta = abs(float(row["amount"]) - float(document_amount))
        amount_ratio = amount_delta / max(float(document_amount), float(row["amount"]), 1.0)
        if amount_ratio <= 0.05:
            score += 35
        elif amount_ratio <= 0.12:
            score += 24
        elif amount_ratio <= 0.25:
            score += 12
        elif amount_ratio <= 0.40:
            score += 5

    if document.get("documentType") == "utility_statement" and date_delta_days is not None and date_delta_days <= 20:
        score += 8

    return score, amount_ratio, date_delta_days


def _match_document(df: pd.DataFrame, document: dict) -> dict:
    candidates = _candidate_rows(df, document)
    if candidates.empty:
        return {
            "matchStatus": "unmatched",
            "matchedVendor": None,
            "matchedDate": None,
            "matchedAmount": None,
            "amountDelta": None,
            "coverageWeight": 0.0,
        }

    scored: list[tuple[float, float | None, int | None, pd.Series]] = []
    for _, row in candidates.iterrows():
        score, amount_ratio, date_delta_days = _score_candidate(row, document)
        scored.append((score, amount_ratio, date_delta_days, row))

    scored.sort(
        key=lambda item: (
            item[0],
            -(item[1] if item[1] is not None else 9),
            -(item[2] if item[2] is not None else 999),
        ),
        reverse=True,
    )
    best_score, amount_ratio, _, row = scored[0]
    document_amount = document.get("totalAmount")
    amount_delta = None
    if document_amount is not None:
        amount_delta = round(abs(float(row["amount"]) - float(document_amount)), 2)

    match_status = "unmatched"
    coverage_weight = 0.0
    if best_score >= 82 and (amount_ratio is None or amount_ratio <= 0.12):
        match_status = "matched"
        coverage_weight = 1.0
    elif best_score >= 55:
        match_status = "partial"
        coverage_weight = 0.6

    return {
        "matchStatus": match_status,
        "matchedVendor": row["vendor"],
        "matchedDate": str(row["date"]),
        "matchedAmount": round(float(row["amount"]), 2),
        "amountDelta": amount_delta,
        "amountRatio": amount_ratio,
        "matchedTxIndex": int(row["txIndex"]),
        "coverageWeight": coverage_weight,
    }


def _severity_sort_value(severity: str) -> int:
    return {
        "high": 3,
        "medium": 2,
        "low": 1,
    }.get(severity, 0)


def _duplicate_key(document: dict) -> tuple[str | None, str | None, str | None, float | None]:
    amount = document.get("totalAmount")
    normalized_amount = round(float(amount), 2) if amount is not None else None
    return (
        _canonicalize_vendor(document.get("issuer")),
        str(document.get("referenceId") or "").strip() or None,
        str(document.get("issueDate") or "").strip() or None,
        normalized_amount,
    )


# ── Forensic transaction-level analysis ───────────────────────────────


def _benford_analysis(amounts: list[float]) -> dict:
    """
    Benford's Law: In naturally occurring financial data, the leading digit
    follows a specific logarithmic distribution. Fabricated data tends to
    have a more uniform or biased distribution. Returns observed vs expected
    frequencies and a chi-squared divergence score.
    """
    leading_digits = []
    for amount in amounts:
        abs_val = abs(amount)
        if abs_val >= 1:
            digit_str = str(abs_val).lstrip("0").lstrip(".")
            if digit_str and digit_str[0].isdigit() and digit_str[0] != "0":
                leading_digits.append(int(digit_str[0]))

    if len(leading_digits) < 10:
        return {
            "testName": "Benford's Law",
            "status": "insufficient_data",
            "severity": "info",
            "detail": f"Only {len(leading_digits)} qualifying transactions — too few for Benford analysis (need at least 10).",
            "observed": {},
            "expected": {},
            "chiSquared": 0.0,
            "sampleSize": len(leading_digits),
        }

    total = len(leading_digits)
    counts = Counter(leading_digits)
    observed = {d: counts.get(d, 0) / total for d in range(1, 10)}
    chi_sq = sum(
        ((observed.get(d, 0) - BENFORD_EXPECTED[d]) ** 2) / BENFORD_EXPECTED[d]
        for d in range(1, 10)
    )

    # Thresholds: chi-squared critical value for 8 df at p=0.05 is 15.51
    if chi_sq > 20:
        severity = "high"
        detail = (
            f"Leading digit distribution deviates significantly from Benford's Law "
            f"(χ² = {chi_sq:.1f}, critical = 15.5). This pattern is commonly seen in "
            f"manually fabricated or estimated transaction data."
        )
    elif chi_sq > 12:
        severity = "medium"
        detail = (
            f"Leading digit distribution shows moderate deviation from Benford's Law "
            f"(χ² = {chi_sq:.1f}). Some transaction amounts may be rounded or estimated."
        )
    else:
        severity = "low"
        detail = (
            f"Leading digit distribution is consistent with Benford's Law "
            f"(χ² = {chi_sq:.1f}). Transaction amounts appear naturally distributed."
        )

    return {
        "testName": "Benford's Law",
        "status": "pass" if severity == "low" else "flag",
        "severity": severity,
        "detail": detail,
        "observed": {str(d): round(observed.get(d, 0) * 100, 1) for d in range(1, 10)},
        "expected": {str(d): round(BENFORD_EXPECTED[d] * 100, 1) for d in range(1, 10)},
        "chiSquared": round(chi_sq, 2),
        "sampleSize": total,
    }


def _round_number_analysis(amounts: list[float]) -> dict:
    """
    Round-number bias: An unusually high percentage of transactions ending
    in .00 or at round hundreds/thousands suggests estimated or fabricated
    data rather than actual invoiced amounts.
    """
    if len(amounts) < 5:
        return {
            "testName": "Round-Number Bias",
            "status": "insufficient_data",
            "severity": "info",
            "detail": "Too few transactions for round-number analysis.",
            "roundPct": 0,
            "roundCount": 0,
            "totalCount": len(amounts),
        }

    round_count = 0
    for amount in amounts:
        abs_val = abs(amount)
        # Check if amount ends in .00 and is a round hundred or thousand
        if abs_val == int(abs_val) and abs_val > 0:
            if abs_val % 100 == 0 or abs_val % 50 == 0:
                round_count += 1

    round_pct = round((round_count / len(amounts)) * 100, 1) if amounts else 0

    if round_pct > 40:
        severity = "high"
        detail = (
            f"{round_pct}% of transactions ({round_count} of {len(amounts)}) are round numbers "
            f"(multiples of $50 or $100). This exceeds the 40% threshold and suggests amounts "
            f"may be estimated rather than actual invoiced values."
        )
    elif round_pct > 25:
        severity = "medium"
        detail = (
            f"{round_pct}% of transactions ({round_count} of {len(amounts)}) are round numbers. "
            f"This is above typical levels and may warrant spot-checking against source documents."
        )
    else:
        severity = "low"
        detail = (
            f"{round_pct}% of transactions ({round_count} of {len(amounts)}) are round numbers. "
            f"This is within expected bounds for typical business transactions."
        )

    return {
        "testName": "Round-Number Bias",
        "status": "pass" if severity == "low" else "flag",
        "severity": severity,
        "detail": detail,
        "roundPct": round_pct,
        "roundCount": round_count,
        "totalCount": len(amounts),
    }


def _temporal_analysis(working: pd.DataFrame) -> dict:
    """
    Temporal anomaly detection: Flags suspicious timing patterns like
    weekend transactions, same-day duplicate amounts for the same vendor,
    and month-end clustering (last 3 days of month).
    """
    valid_dates = working[working["txDate"].notna()].copy()
    if valid_dates.empty:
        return {
            "testName": "Temporal Patterns",
            "status": "insufficient_data",
            "severity": "info",
            "detail": "No valid dates found in transactions.",
            "weekendTxCount": 0,
            "weekendTxPct": 0,
            "sameDayDuplicates": 0,
            "monthEndClusterPct": 0,
            "findings": [],
        }

    total = len(valid_dates)
    findings = []

    # Weekend transactions
    valid_dates.loc[:, "dayOfWeek"] = valid_dates["txDate"].dt.dayofweek
    weekend_rows = valid_dates[valid_dates["dayOfWeek"] >= 5]
    weekend_count = len(weekend_rows)
    weekend_pct = round((weekend_count / total) * 100, 1)
    if weekend_pct > 15:
        findings.append(
            f"{weekend_count} transactions ({weekend_pct}%) recorded on weekends — "
            f"unusual for typical business operations."
        )

    # Same-day, same-vendor duplicate amounts
    same_day_dups = 0
    if "matchVendor" in valid_dates.columns:
        date_vendor_amount = valid_dates.groupby(
            [valid_dates["txDate"].dt.date, "matchVendor", "amount"]
        ).size()
        same_day_dups = int(date_vendor_amount[date_vendor_amount > 1].sum())
        if same_day_dups > 0:
            findings.append(
                f"{same_day_dups} transactions share the same date, vendor, and amount — "
                f"potential duplicate entries or split-billing pattern."
            )

    # Month-end clustering (last 3 days)
    valid_dates.loc[:, "dayOfMonth"] = valid_dates["txDate"].dt.day
    valid_dates.loc[:, "daysInMonth"] = valid_dates["txDate"].dt.days_in_month
    month_end_rows = valid_dates[
        valid_dates["dayOfMonth"] >= (valid_dates["daysInMonth"] - 2)
    ]
    month_end_pct = round((len(month_end_rows) / total) * 100, 1)
    expected_month_end_pct = round((3 / 30) * 100, 1)  # ~10% expected
    if month_end_pct > 25:
        findings.append(
            f"{month_end_pct}% of transactions cluster in the last 3 days of the month "
            f"(expected ~{expected_month_end_pct}%). May indicate month-end stuffing."
        )

    if findings:
        severity = "high" if len(findings) >= 3 else "medium" if len(findings) >= 2 else "low"
        detail = " ".join(findings)
    else:
        severity = "low"
        detail = (
            f"Transaction dates are distributed normally. "
            f"Weekend activity: {weekend_pct}%, month-end clustering: {month_end_pct}%."
        )

    return {
        "testName": "Temporal Patterns",
        "status": "pass" if not findings else "flag",
        "severity": severity,
        "detail": detail,
        "weekendTxCount": weekend_count,
        "weekendTxPct": weekend_pct,
        "sameDayDuplicates": same_day_dups,
        "monthEndClusterPct": month_end_pct,
        "findings": findings,
    }


def _run_transaction_anomalies(df: pd.DataFrame) -> list[dict]:
    """
    Run all forensic analyses on the transaction ledger.
    These work regardless of whether supporting documents are uploaded.
    """
    working = _prepare_dataframe(df)
    amounts = [float(a) for a in working["amount"] if pd.notna(a)]

    return [
        _benford_analysis(amounts),
        _round_number_analysis(amounts),
        _temporal_analysis(working),
    ]


def analyze_supporting_documents(df: pd.DataFrame, documents: list[dict]) -> dict:
    # ── Always run transaction-level forensic analysis ──
    transaction_anomalies = _run_transaction_anomalies(df)

    # ── Compute extra risk from transaction anomalies ──
    anomaly_risk = 0
    for anomaly in transaction_anomalies:
        if anomaly["status"] == "flag":
            if anomaly["severity"] == "high":
                anomaly_risk += 12
            elif anomaly["severity"] == "medium":
                anomaly_risk += 6

    if not documents:
        # Even without documents, report transaction-level findings
        tx_severity = max(
            (a["severity"] for a in transaction_anomalies if a["status"] == "flag"),
            default="low",
            key=lambda s: _severity_sort_value(s),
        )
        tx_risk = min(anomaly_risk + 5, 100)

        flagged_tests = [a for a in transaction_anomalies if a["status"] == "flag"]
        if flagged_tests:
            summary = (
                f"No supporting documents uploaded — document-to-ledger matching was skipped. "
                f"However, forensic analysis of {len(df)} ledger transactions detected "
                f"{len(flagged_tests)} anomal{'y' if len(flagged_tests) == 1 else 'ies'} "
                f"in the transaction data."
            )
        else:
            summary = (
                f"No supporting documents uploaded. Forensic analysis of {len(df)} ledger "
                f"transactions found no material anomalies in amount distribution or timing."
            )

        return {
            "overallRisk": tx_severity if flagged_tests else "not_assessed",
            "riskScore": tx_risk if flagged_tests else 0,
            "summary": summary,
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
            "transactionAnomalies": transaction_anomalies,
        }

    working = _prepare_dataframe(df)
    flags: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []

    reference_counter = Counter(
        _duplicate_key(document)
        for document in documents
        if document.get("referenceId")
    )
    duplicate_documents = 0

    for document in documents:
        match_result = _match_document(working, document)
        review = {
            "fileName": document["fileName"],
            "documentType": document.get("documentType", "unknown"),
            "issuer": document.get("issuer"),
            "issueDate": document.get("issueDate"),
            "referenceId": document.get("referenceId"),
            "totalAmount": document.get("totalAmount"),
            "matchStatus": match_result["matchStatus"],
            "matchedVendor": match_result.get("matchedVendor"),
            "matchedDate": match_result.get("matchedDate"),
            "matchedAmount": match_result.get("matchedAmount"),
            "amountDelta": match_result.get("amountDelta"),
            "parserNotes": document.get("parserNotes", []),
        }
        reviews.append(review)

        duplicate_key = _duplicate_key(document)
        if document.get("referenceId") and reference_counter[duplicate_key] > 1:
            duplicate_documents += 1
            flags.append(
                _flag(
                    "high",
                    "duplicate_document",
                    "Duplicate supporting document reference detected",
                    (
                        f"{document['referenceId']} appears on multiple uploaded documents with the same issuer, "
                        f"issue date, and amount."
                    ),
                    document_name=document["fileName"],
                    vendor=document.get("issuer"),
                    document_amount=document.get("totalAmount"),
                    recommended_action="Confirm the document was not uploaded twice and verify the original source file.",
                )
            )

        math_delta = document.get("mathDelta")
        if math_delta is not None and abs(float(math_delta)) > 1.5:
            flags.append(
                _flag(
                    "high",
                    "document_math_mismatch",
                    "Document totals do not reconcile internally",
                    f"Line items and taxes differ from the stated total by ${abs(float(math_delta)):.2f}.",
                    document_name=document["fileName"],
                    vendor=document.get("issuer"),
                    document_amount=document.get("totalAmount"),
                    recommended_action="Review the PDF for alterations and compare against the original invoice or receipt.",
                )
            )

        for note in document.get("parserNotes", []):
            flags.append(
                _flag(
                    "low",
                    "parser_gap",
                    "Document requires manual verification",
                    note,
                    document_name=document["fileName"],
                    vendor=document.get("issuer"),
                    document_amount=document.get("totalAmount"),
                    recommended_action="Open the uploaded document and confirm the missing fields manually.",
                )
            )

        if match_result["matchStatus"] == "unmatched":
            flags.append(
                _flag(
                    "medium",
                    "unmatched_document",
                    "Uploaded document could not be tied to a ledger transaction",
                    "No sufficiently similar vendor/date/amount combination was found in the uploaded transaction ledger.",
                    document_name=document["fileName"],
                    vendor=document.get("issuer"),
                    transaction_date=document.get("issueDate"),
                    document_amount=document.get("totalAmount"),
                    recommended_action="Confirm the transaction exists in the CSV and review whether the document belongs to another period or vendor.",
                )
            )
        elif match_result["matchStatus"] == "partial":
            amount_ratio = match_result.get("amountRatio") or 0.0
            severity = "high" if amount_ratio > 0.25 else "medium"
            flags.append(
                _flag(
                    severity,
                    "amount_mismatch",
                    "Document and ledger amount do not align cleanly",
                    (
                        f"Closest ledger amount was ${match_result['matchedAmount']:.2f}, "
                        f"while the uploaded document totals ${document.get('totalAmount') or 0:.2f}."
                    ),
                    document_name=document["fileName"],
                    vendor=match_result.get("matchedVendor") or document.get("issuer"),
                    transaction_date=match_result.get("matchedDate"),
                    document_amount=document.get("totalAmount"),
                    matched_amount=match_result.get("matchedAmount"),
                    recommended_action="Check whether the ledger entry is batched, duplicated, or missing tax/shipping components.",
                )
            )

    for vendor in sorted({document.get("canonicalVendor") for document in documents if document.get("canonicalVendor")}):
        vendor_rows = working[working["matchVendor"] == vendor]
        if vendor_rows.empty:
            continue

        supported_docs = [
            review for review, document in zip(reviews, documents)
            if document.get("canonicalVendor") == vendor and review["matchStatus"] in {"matched", "partial"}
        ]
        if len(vendor_rows) >= 4 and not supported_docs:
            flags.append(
                _flag(
                    "medium",
                    "coverage_gap",
                    "Supporting document coverage is thin for a recurring vendor",
                    (
                        f"No uploaded document was matched to "
                        f"{len(vendor_rows)} ledger entries for {vendor_rows.iloc[0]['vendor']}."
                    ),
                    vendor=vendor_rows.iloc[0]["vendor"],
                    matched_amount=round(float(vendor_rows["amount"].sum()), 2),
                    recommended_action="Upload a fuller sample of recurring invoices or bills for this vendor to strengthen assurance coverage.",
                )
            )
        elif len(vendor_rows) >= 8 and len(supported_docs) == 1:
            flags.append(
                _flag(
                    "low",
                    "coverage_gap",
                    "Supporting document coverage is thin for a recurring vendor",
                    (
                        f"Only 1 uploaded document currently supports "
                        f"{len(vendor_rows)} ledger entries for {vendor_rows.iloc[0]['vendor']}."
                    ),
                    vendor=vendor_rows.iloc[0]["vendor"],
                    matched_amount=round(float(vendor_rows["amount"].sum()), 2),
                    recommended_action="Upload a broader sample of recurring invoices or statements for this vendor if you need stronger audit support.",
                )
            )

    matched_documents = sum(1 for review in reviews if review["matchStatus"] == "matched")
    partial_matches = sum(1 for review in reviews if review["matchStatus"] == "partial")
    unmatched_documents = sum(1 for review in reviews if review["matchStatus"] == "unmatched")

    reviewed_vendors = {
        document.get("canonicalVendor")
        for document in documents
        if document.get("canonicalVendor")
    }
    reviewed_vendor_rows = working[working["matchVendor"].isin(reviewed_vendors)] if reviewed_vendors else working.iloc[0:0]
    reviewed_vendor_spend = round(float(reviewed_vendor_rows["amount"].sum()), 2) if not reviewed_vendor_rows.empty else 0.0

    verified_spend = 0.0
    for review, document in zip(reviews, documents):
        matched_amount = review.get("matchedAmount")
        document_amount = document.get("totalAmount")
        if matched_amount is None:
            continue
        supported_amount = min(matched_amount, document_amount) if document_amount is not None else matched_amount
        weight = 1.0 if review["matchStatus"] == "matched" else 0.6 if review["matchStatus"] == "partial" else 0.0
        verified_spend += supported_amount * weight
    verified_spend = round(verified_spend, 2)

    verified_spend_pct = 0
    if reviewed_vendor_spend > 0:
        verified_spend_pct = int(round((verified_spend / reviewed_vendor_spend) * 100))

    risk_score = 8 + anomaly_risk
    for flag in flags:
        risk_score += SEVERITY_WEIGHTS.get(flag["severity"], 0)

    if reviews:
        coverage_ratio = (matched_documents + partial_matches) / len(reviews)
        if coverage_ratio < 0.35:
            risk_score += 14
        elif coverage_ratio < 0.65:
            risk_score += 8

    risk_score = min(risk_score, 100)

    if risk_score >= 60:
        overall_risk = "high"
    elif risk_score >= 30:
        overall_risk = "medium"
    else:
        overall_risk = "low"

    flags.sort(
        key=lambda item: (
            _severity_sort_value(item["severity"]),
            item["title"],
        ),
        reverse=True,
    )

    flagged_anomalies = [a for a in transaction_anomalies if a["status"] == "flag"]
    anomaly_note = ""
    if flagged_anomalies:
        anomaly_note = (
            f" Additionally, forensic analysis flagged {len(flagged_anomalies)} "
            f"transaction-level anomal{'y' if len(flagged_anomalies) == 1 else 'ies'}."
        )

    if flags:
        summary = (
            f"Document assurance reviewed {len(reviews)} uploaded file(s) and rated fraud risk {overall_risk.upper()} "
            f"at {risk_score}/100. {matched_documents} document(s) matched cleanly, {partial_matches} were partial, "
            f"and {unmatched_documents} require follow-up.{anomaly_note}"
        )
    else:
        summary = (
            f"Document assurance reviewed {len(reviews)} uploaded file(s) with {overall_risk.upper()} risk findings. "
            f"{matched_documents} matched cleanly and no material document anomalies were detected.{anomaly_note}"
        )

    return {
        "overallRisk": overall_risk,
        "riskScore": risk_score,
        "summary": summary,
        "supportingDocsReviewed": len(reviews),
        "matchedDocuments": matched_documents,
        "partialMatches": partial_matches,
        "unmatchedDocuments": unmatched_documents,
        "duplicateDocuments": duplicate_documents,
        "verifiedSpendAmount": verified_spend,
        "reviewedVendorSpendAmount": reviewed_vendor_spend,
        "verifiedSpendPct": verified_spend_pct,
        "flags": flags[:8],
        "documents": reviews,
        "transactionAnomalies": transaction_anomalies,
    }
