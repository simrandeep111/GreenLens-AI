"""
Shared Moorcheh client for narrative and chat generation.
"""

from __future__ import annotations

import json
import traceback

import httpx

from core.config import MOORCHEH_API_KEY, MOORCHEH_BASE_URL, MOORCHEH_MODEL

FALLBACK_MODEL = "anthropic.claude-sonnet-4-20250514-v1:0"


def _extract_llm_payload(data: dict) -> str:
    structured = data.get("structuredData")
    if isinstance(structured, dict):
        return json.dumps(structured)

    answer = data.get("answer", "")
    return answer if isinstance(answer, str) else ""


def call_moorcheh_answer(
    prompt: str,
    *,
    namespace: str = "",
    temperature: float = 0.2,
    timeout: float = 180.0,
) -> str:
    """
    Call Moorcheh's answer endpoint and retry once on model timeout.
    Returns the answer payload as a string or an empty string on failure.
    """
    headers = {
        "x-api-key": MOORCHEH_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "namespace": namespace,
        "query": prompt,
        "aiModel": MOORCHEH_MODEL,
        "temperature": temperature,
    }

    try:
        response = httpx.post(
            f"{MOORCHEH_BASE_URL}/answer",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return _extract_llm_payload(response.json())

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 504 and payload["aiModel"] == MOORCHEH_MODEL:
            print("[LLM] 504 Gateway Timeout. Retrying with Sonnet 4.")
            payload["aiModel"] = FALLBACK_MODEL
            try:
                response = httpx.post(
                    f"{MOORCHEH_BASE_URL}/answer",
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                return _extract_llm_payload(response.json())
            except Exception as retry_error:
                print(f"[LLM ERROR] Fallback failed: {retry_error}")
                traceback.print_exc()
                return ""

        print(f"[LLM ERROR] HTTP Status Error: {exc}")
        traceback.print_exc()
        return ""
    except Exception as exc:
        print(f"[LLM ERROR] {exc}")
        traceback.print_exc()
        return ""
