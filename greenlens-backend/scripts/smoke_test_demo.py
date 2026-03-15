"""
End-to-end API smoke tests for the GreenLens demo flows.

Runs both supported demo scenarios:
1. CSV + supporting documents
2. CSV only (no supporting documents)

The LLM calls are patched to return empty strings so report and chat fall back
to deterministic text without making network calls.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402
import services.report_generator as report_generator  # noqa: E402
import services.report_chat_service as report_chat_service  # noqa: E402


DATA_DIR = BACKEND_DIR / "demo_data"
MAPLE_DOCS_DIR = DATA_DIR / "support_docs" / "maple_leaf_catering"


def _disable_llm_calls() -> None:
    report_generator.call_moorcheh_answer = lambda *args, **kwargs: ""
    report_chat_service.call_moorcheh_answer = lambda *args, **kwargs: ""


def _wait_for_completion(client: TestClient, job_id: str, timeout_seconds: float = 30.0) -> dict:
    deadline = time.time() + timeout_seconds
    last_status: dict | None = None

    while time.time() < deadline:
        response = client.get(f"/api/status/{job_id}")
        response.raise_for_status()
        last_status = response.json()

        if last_status["status"] == "complete":
            return last_status
        if last_status["status"] in {"error", "failed"}:
            raise AssertionError(f"Job {job_id} failed: {last_status}")

        time.sleep(0.25)

    raise TimeoutError(f"Job {job_id} did not complete in time. Last status: {last_status}")


def _upload_and_run(
    client: TestClient,
    *,
    csv_path: Path,
    pdf_paths: list[Path],
    company: dict,
    governance_answers: list[str],
) -> tuple[dict, dict]:
    files = [
        ("csv_file", (csv_path.name, csv_path.read_bytes(), "text/csv")),
    ]
    files.extend(
        ("pdf_files", (pdf_path.name, pdf_path.read_bytes(), "application/pdf"))
        for pdf_path in pdf_paths
    )

    upload_response = client.post("/api/upload", files=files)
    upload_response.raise_for_status()
    upload_id = upload_response.json()["uploadId"]

    analyze_response = client.post(
        "/api/analyze",
        json={
            "uploadId": upload_id,
            "company": company,
            "governance_answers": governance_answers,
        },
    )
    analyze_response.raise_for_status()
    job_id = analyze_response.json()["jobId"]

    status = _wait_for_completion(client, job_id)

    report_response = client.get(f"/api/report/{job_id}")
    report_response.raise_for_status()
    report = report_response.json()

    return status, report


def _assert_core_report_shape(report: dict) -> None:
    assert report["company"]["name"], "company.name should be populated"
    assert "benchmark" in report["emissions"], "emissions.benchmark should always exist"
    assert "fraudAnalysis" in report, "fraudAnalysis should always exist"
    assert "transactionAnomalies" in report["fraudAnalysis"], "transactionAnomalies should always exist"
    assert len(report["fraudAnalysis"]["transactionAnomalies"]) == 3, "expected 3 forensic anomaly tests"
    assert "reportSections" in report, "reportSections should always exist"
    assert report["reportSections"]["fraudNarrative"], "fraudNarrative should always be populated"


def run_smoke_tests() -> None:
    _disable_llm_calls()
    client = TestClient(app)

    root_response = client.get("/")
    root_response.raise_for_status()
    root = root_response.json()
    assert root["status"] == "ok"
    assert root["bootId"]

    with_docs_company = {
        "name": "Maple Leaf Catering Co.",
        "province": "Ontario",
        "industry": "Food & Beverage",
        "employees": 48,
        "revenue": "$2,400,000",
    }
    governance_answers = ["No", "No", "No", "No"]

    with_docs_status, with_docs_report = _upload_and_run(
        client,
        csv_path=DATA_DIR / "demo_maple_leaf_catering.csv",
        pdf_paths=sorted(MAPLE_DOCS_DIR.glob("*.pdf")),
        company=with_docs_company,
        governance_answers=governance_answers,
    )
    assert with_docs_status["progress"] == 100
    assert with_docs_status["fraudAlert"]["hasIssues"] is True
    assert with_docs_status["fraudAlert"]["flagCount"] >= 1
    assert len(with_docs_status["fraudAlert"]["topFindings"]) == len(
        set(item.casefold() for item in with_docs_status["fraudAlert"]["topFindings"])
    )
    _assert_core_report_shape(with_docs_report)
    assert with_docs_report["fraudAnalysis"]["supportingDocsReviewed"] == 6
    assert len(with_docs_report["fraudAnalysis"]["documents"]) == 6
    assert with_docs_report["fraudAnalysis"]["duplicateDocuments"] >= 2
    assert with_docs_report["fraudAnalysis"]["summary"]

    chat_response = client.post(
        f"/api/report-chat/{with_docs_status['jobId']}",
        json={
            "question": "What fraud signals were detected?",
            "history": [],
        },
    )
    chat_response.raise_for_status()
    chat_payload = chat_response.json()
    assert chat_payload["answer"]
    assert isinstance(chat_payload["citations"], list)

    without_docs_company = {
        "name": "TechNorth Solutions",
        "province": "Ontario",
        "industry": "Technology",
        "employees": 32,
        "revenue": "$3,800,000",
    }
    without_docs_status, without_docs_report = _upload_and_run(
        client,
        csv_path=DATA_DIR / "demo_technorth_solutions.csv",
        pdf_paths=[],
        company=without_docs_company,
        governance_answers=governance_answers,
    )
    assert without_docs_status["progress"] == 100
    _assert_core_report_shape(without_docs_report)
    assert without_docs_report["fraudAnalysis"]["supportingDocsReviewed"] == 0
    assert without_docs_report["fraudAnalysis"]["documents"] == []
    assert "No supporting documents uploaded" in without_docs_report["fraudAnalysis"]["summary"]
    assert "No supporting documents were uploaded" in without_docs_report["reportSections"]["fraudNarrative"]

    print("Smoke tests passed:")
    print("- CSV + supporting documents flow")
    print("- CSV-only flow")
    print("- Report API shape normalization")
    print("- Report chat fallback on grounded report data")


if __name__ == "__main__":
    run_smoke_tests()
