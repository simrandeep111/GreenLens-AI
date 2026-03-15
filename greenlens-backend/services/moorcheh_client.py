"""
Shared Moorcheh client for narrative and chat generation.
"""

from __future__ import annotations

import json
import time
import traceback

import httpx

from core.config import MOORCHEH_API_KEY, MOORCHEH_BASE_URL, MOORCHEH_MODEL

TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}


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
    Call Moorcheh's answer endpoint and retry the configured model on transient failures.
    Returns the answer payload as a string or an empty string on failure.
    """
    if not MOORCHEH_API_KEY:
        print("[LLM ERROR] MOORCHEH_API_KEY is missing.")
        return ""

    headers = {
        "x-api-key": MOORCHEH_API_KEY,
        "Content-Type": "application/json",
    }
    model_name = MOORCHEH_MODEL
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        payload = {
            "namespace": namespace,
            "query": prompt,
            "aiModel": model_name,
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
            status_code = exc.response.status_code
            is_transient = status_code in TRANSIENT_STATUS_CODES

            if is_transient and attempt < max_attempts:
                print(
                    f"[LLM] Model {model_name} returned HTTP {status_code}. "
                    f"Retrying attempt {attempt + 1}/{max_attempts}."
                )
                time.sleep(1.2 * attempt)
                continue

            print(f"[LLM ERROR] HTTP Status Error: {exc}")
            traceback.print_exc()
            return ""

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            if attempt < max_attempts:
                print(
                    f"[LLM] Model {model_name} request failed with {exc.__class__.__name__}. "
                    f"Retrying attempt {attempt + 1}/{max_attempts}."
                )
                time.sleep(1.2 * attempt)
                continue

            print(f"[LLM ERROR] {exc}")
            traceback.print_exc()
            return ""

        except Exception as exc:
            print(f"[LLM ERROR] {exc}")
            traceback.print_exc()
            return ""

    return ""
