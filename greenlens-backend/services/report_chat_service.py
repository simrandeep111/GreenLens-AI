"""
Grounded ESG report chat service using lightweight retrieval plus Moorcheh generation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from services.moorcheh_client import call_moorcheh_answer
from services.retrieval_service import retrieve_compliance, retrieve_grants

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i",
    "if", "in", "into", "is", "it", "me", "of", "on", "or", "our", "show", "that",
    "the", "this", "to", "us", "what", "which", "why", "with", "you", "your",
}

TOPIC_KEYWORDS = {
    "emissions": {"emission", "emissions", "scope", "carbon", "footprint", "intensity", "heating", "electricity"},
    "compliance": {"compliance", "cbca", "osfi", "b-15", "gri", "ghg", "tcfd", "disclosure", "regulation"},
    "funding": {"grant", "grants", "funding", "rebate", "credit", "incentive", "sred", "sr&ed", "program"},
    "actions": {"action", "actions", "recommendation", "recommendations", "improve", "priority", "next"},
    "score": {"score", "grade", "environmental", "social", "governance", "advanced", "leading", "emerging"},
}


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    title: str
    source_label: str
    content: str
    section_id: str | None
    topic: str
    base_score: float = 0.0


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9&\-]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    }


def _detect_topics(tokens: set[str]) -> set[str]:
    topics = {topic for topic, keywords in TOPIC_KEYWORDS.items() if tokens & keywords}
    return topics or {"emissions", "compliance", "funding", "actions", "score"}


def _first_sentences(text: str, max_len: int = 220) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_len:
        return compact
    trimmed = compact[:max_len].rsplit(" ", 1)[0]
    return f"{trimmed}..."


def _build_report_chunks(report: dict) -> list[RetrievedChunk]:
    company = report["company"]
    score = report["score"]
    emissions = report["emissions"]
    sections = report["reportSections"]

    chunks = [
        RetrievedChunk(
            chunk_id="report-overview",
            title="Report overview",
            source_label="Report data",
            content=(
                f"{company['name']} is a {company['industry']} company in {company['province']} with "
                f"{company['employees']} employees and revenue of {company['revenue']}. "
                f"It has an ESG score of {score['total']}/100 with grade {score['grade']}. "
                f"Total emissions are {emissions['totalTCO2e']} tCO2e with intensity "
                f"{emissions['intensityKgPerRevenue']} kgCO2e per $1,000 revenue."
            ),
            section_id="exec",
            topic="score",
            base_score=1.2,
        ),
        RetrievedChunk(
            chunk_id="report-executive-summary",
            title="Executive Summary",
            source_label="Report section",
            content=sections["executiveSummary"],
            section_id="exec",
            topic="score",
            base_score=1.1,
        ),
        RetrievedChunk(
            chunk_id="report-emissions-narrative",
            title="Emissions Overview",
            source_label="Report section",
            content=sections["emissionsNarrative"],
            section_id="emissions",
            topic="emissions",
            base_score=1.1,
        ),
        RetrievedChunk(
            chunk_id="report-compliance-narrative",
            title="Compliance & Regulatory Insights",
            source_label="Report section",
            content=sections["complianceNarrative"],
            section_id="compliance",
            topic="compliance",
            base_score=1.1,
        ),
        RetrievedChunk(
            chunk_id="report-funding-narrative",
            title="Funding Opportunities",
            source_label="Report section",
            content=sections["fundingNarrative"],
            section_id="funding",
            topic="funding",
            base_score=1.1,
        ),
        RetrievedChunk(
            chunk_id="report-actions-narrative",
            title="Recommended Actions",
            source_label="Report section",
            content=sections["actionsNarrative"],
            section_id="actions",
            topic="actions",
            base_score=1.1,
        ),
    ]

    for index, item in enumerate(report.get("compliance", []), start=1):
        chunks.append(
            RetrievedChunk(
                chunk_id=f"compliance-{index}",
                title=item["framework"],
                source_label="Compliance item",
                content=f"Status: {item['status']}. {item['detail']}",
                section_id="compliance",
                topic="compliance",
                base_score=0.95,
            )
        )

    for index, item in enumerate(report.get("grants", []), start=1):
        chunks.append(
            RetrievedChunk(
                chunk_id=f"grant-{index}",
                title=item["name"],
                source_label="Grant",
                content=f"Amount: {item['amount']}. Tags: {', '.join(item.get('tags', []))}. {item['description']}",
                section_id="funding",
                topic="funding",
                base_score=0.95,
            )
        )

    for index, item in enumerate(report.get("recommendations", []), start=1):
        chunks.append(
            RetrievedChunk(
                chunk_id=f"recommendation-{index}",
                title=f"Recommendation {index}",
                source_label="Recommendation",
                content=f"{item['text']}. Expected impact: {item['impactLabel']}.",
                section_id="actions",
                topic="actions",
                base_score=0.95,
            )
        )

    for index, item in enumerate(report["emissions"].get("breakdown", []), start=1):
        chunks.append(
            RetrievedChunk(
                chunk_id=f"emission-breakdown-{index}",
                title=item["category"],
                source_label="Emissions breakdown",
                content=(
                    f"{item['category']} is {item['tCO2e']} tCO2e in {item['scope']} and "
                    f"represents {item['percentOfTotal']}% of total emissions."
                ),
                section_id="emissions",
                topic="emissions",
                base_score=0.85,
            )
        )

    return chunks


def _build_knowledge_chunks(report: dict) -> list[RetrievedChunk]:
    company = report["company"]
    compliance_docs = retrieve_compliance(company["province"], company["industry"])
    grant_docs = retrieve_grants(company["province"], company["industry"], company["employees"])

    chunks: list[RetrievedChunk] = []
    for index, doc in enumerate(compliance_docs, start=1):
        meta = doc.get("metadata", {})
        chunks.append(
            RetrievedChunk(
                chunk_id=f"knowledge-compliance-{index}",
                title=meta.get("framework", "Compliance guidance"),
                source_label="Knowledge base",
                content=doc.get("content", ""),
                section_id="compliance",
                topic="compliance",
                base_score=0.7,
            )
        )

    for index, doc in enumerate(grant_docs, start=1):
        meta = doc.get("metadata", {})
        chunks.append(
            RetrievedChunk(
                chunk_id=f"knowledge-grant-{index}",
                title=meta.get("program_name", "Funding guidance"),
                source_label="Knowledge base",
                content=doc.get("content", ""),
                section_id="funding",
                topic="funding",
                base_score=0.7,
            )
        )

    return chunks


def retrieve_chat_context(report: dict, question: str, limit: int = 6) -> list[RetrievedChunk]:
    question_tokens = _tokenize(question)
    active_topics = _detect_topics(question_tokens)
    chunks = _build_report_chunks(report) + _build_knowledge_chunks(report)

    scored: list[tuple[float, RetrievedChunk]] = []
    question_lower = question.lower()
    for chunk in chunks:
        content_tokens = _tokenize(f"{chunk.title} {chunk.content}")
        overlap = question_tokens & content_tokens
        score = chunk.base_score
        score += len(overlap) * 1.35

        if chunk.topic in active_topics:
            score += 2.0

        if any(keyword in chunk.title.lower() for keyword in overlap):
            score += 0.8

        if question_lower in chunk.content.lower():
            score += 1.5

        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def _clean_json(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    return cleaned.strip()


def _parse_chat_response(raw: str) -> tuple[str, list[str]]:
    cleaned = _clean_json(raw)
    payload = json.loads(cleaned, strict=False)

    answer = str(payload.get("answer", "")).strip()
    citation_ids = payload.get("citationIds", [])
    if not isinstance(citation_ids, list):
        citation_ids = []

    return answer, [str(item).strip() for item in citation_ids if str(item).strip()]


def _format_history(history: list[dict]) -> str:
    recent = history[-6:]
    if not recent:
        return "No previous chat turns."
    return "\n".join(f"{item['role'].title()}: {item['content']}" for item in recent)


def _build_chat_prompt(question: str, history: list[dict], chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for chunk in chunks:
        context_blocks.append(
            f"[{chunk.chunk_id}] {chunk.title} ({chunk.source_label})\n{chunk.content}"
        )

    context_text = "\n\n".join(context_blocks)
    return f"""You are GreenLens ESG Copilot, a grounded assistant for a generated ESG report.
Answer the user's question using ONLY the supplied context.

Return ONLY valid JSON with this exact schema:
{{
  "answer": "2-5 sentence helpful answer grounded in the context.",
  "citationIds": ["chunk-id-1", "chunk-id-2"]
}}

Rules:
1. Do not invent facts not supported by context.
2. If the context is insufficient, say so clearly and answer with the closest supported guidance.
3. Prefer report-specific evidence first, then knowledge-base guidance.
4. Use at most 3 citationIds and only cite ids that appear below.
5. Do not use markdown fences.

Conversation so far:
{_format_history(history)}

User question:
{question}

Relevant context:
{context_text}
"""


def _fallback_chat_answer(question: str, chunks: list[RetrievedChunk]) -> tuple[str, list[RetrievedChunk]]:
    top_chunks = chunks[:2]
    if not top_chunks:
        return (
            "I do not have enough grounded context in the report to answer that confidently.",
            [],
        )

    snippets = " ".join(
        _first_sentences(chunk.content, max_len=140)
        for chunk in top_chunks
    )
    return (
        f"I could not generate a full AI answer, but the most relevant report evidence suggests: {snippets}",
        top_chunks,
    )


def answer_report_question(report: dict, question: str, history: list[dict]) -> dict:
    chunks = retrieve_chat_context(report, question)
    if not chunks:
        return {
            "answer": "I do not have enough report context to answer that question.",
            "answerSource": "fallback",
            "citations": [],
        }

    prompt = _build_chat_prompt(question, history, chunks)
    raw = call_moorcheh_answer(prompt, temperature=0.2, timeout=120.0)

    cited_chunks = chunks[:2]
    answer_source = "fallback"
    answer_text = ""
    if raw:
        try:
            answer_text, citation_ids = _parse_chat_response(raw)
            if answer_text:
                citation_lookup = {chunk.chunk_id: chunk for chunk in chunks}
                resolved = [
                    citation_lookup[citation_id]
                    for citation_id in citation_ids
                    if citation_id in citation_lookup
                ]
                if resolved:
                    cited_chunks = resolved[:3]
                answer_source = "llm"
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"[CHAT] Failed to parse LLM chat JSON: {exc}")
            print(f"[CHAT] Raw response: {raw[:500]}")

    if not answer_text:
        answer_text, cited_chunks = _fallback_chat_answer(question, chunks)

    return {
        "answer": answer_text,
        "answerSource": answer_source,
        "citations": [
            {
                "chunkId": chunk.chunk_id,
                "title": chunk.title,
                "sourceLabel": chunk.source_label,
                "excerpt": _first_sentences(chunk.content),
                "sectionId": chunk.section_id,
            }
            for chunk in cited_chunks
        ],
    }
