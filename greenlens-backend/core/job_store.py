"""
In-memory job store for tracking pipeline progress.
Thread-safe via a simple lock.
"""

from __future__ import annotations
import threading
from typing import Any, Dict, List, Optional

_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}


def create_job(job_id: str, upload_id: str, company: dict, governance_answers: List[str]) -> None:
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "upload_id": upload_id,
            "company": company,
            "governance_answers": governance_answers,
            "status": "queued",
            "current_step": 0,
            "step_label": "Queued",
            "progress": 0,
            "error": None,
            "result": None,
        }


def update_step(job_id: str, step: int, label: str, progress: int) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "running"
            _jobs[job_id]["current_step"] = step
            _jobs[job_id]["step_label"] = label
            _jobs[job_id]["progress"] = progress


def complete_job(job_id: str, result: dict) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "complete"
            _jobs[job_id]["current_step"] = 7
            _jobs[job_id]["step_label"] = "Complete"
            _jobs[job_id]["progress"] = 100
            _jobs[job_id]["result"] = result


def fail_job(job_id: str, error: str) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = error


def get_job(job_id: str) -> Optional[dict]:
    with _lock:
        return _jobs.get(job_id)
