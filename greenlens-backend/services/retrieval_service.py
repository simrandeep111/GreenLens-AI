"""
Retrieval service — lightweight local knowledge retrieval for compliance + grants.
Uses tagged JSON documents, filtered by province/industry.
No external vector database — just structured local files.
"""

from __future__ import annotations
import json
from pathlib import Path
from core.config import KNOWLEDGE_DIR


def _load_corpus(subdir: str) -> list[dict]:
    """Load all JSON docs from a knowledge subdirectory."""
    corpus_dir = KNOWLEDGE_DIR / subdir
    docs = []
    if not corpus_dir.exists():
        return docs
    for f in sorted(corpus_dir.glob("*.json")):
        with open(f) as fh:
            docs.append(json.load(fh))
    return docs


def _score_relevance(doc: dict, province: str, industry: str) -> float:
    """Simple relevance scoring based on metadata match."""
    score = 0.5  # base relevance for being in the corpus
    meta = doc.get("metadata", {})

    # Province match
    doc_province = meta.get("province", "Canada").lower()
    if doc_province == province.lower() or doc_province in ("canada", "federal", "all"):
        score += 0.3

    # Industry match
    doc_industry = meta.get("industry", "general").lower()
    if doc_industry == industry.lower() or doc_industry == "general":
        score += 0.2

    return score


def retrieve_compliance(province: str, industry: str, top_k: int = 4) -> list[dict]:
    """Retrieve the most relevant compliance documents."""
    docs = _load_corpus("compliance")
    scored = [(doc, _score_relevance(doc, province, industry)) for doc in docs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]


def retrieve_grants(province: str, industry: str, employees: int, top_k: int = 4) -> list[dict]:
    """Retrieve the most relevant grant/funding documents."""
    docs = _load_corpus("grants")
    scored = []
    for doc in docs:
        relevance = _score_relevance(doc, province, industry)
        meta = doc.get("metadata", {})
        # Bonus if company size matches
        size = meta.get("company_size", "").lower()
        if size in ("smb", "sme") and employees < 200:
            relevance += 0.1
        scored.append((doc, relevance))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]


def format_compliance_context(docs: list[dict]) -> str:
    """Format compliance docs into a text block for the LLM prompt."""
    lines = []
    for doc in docs:
        meta = doc.get("metadata", {})
        framework = meta.get("framework", "Unknown")
        lines.append(f"## {framework}")
        lines.append(doc.get("content", ""))
        lines.append("")
    return "\n".join(lines)


def format_grants_context(docs: list[dict]) -> str:
    """Format grant docs into a text block for the LLM prompt."""
    lines = []
    for doc in docs:
        meta = doc.get("metadata", {})
        name = meta.get("program_name", "Unknown")
        lines.append(f"## {name}")
        lines.append(doc.get("content", ""))
        lines.append("")
    return "\n".join(lines)
