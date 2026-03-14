"""
Supporting document parsing for uploaded PDF bills, receipts, and invoices.
Uses lightweight PDF text extraction so the demo documents and many digital PDFs
can be structured without external OCR dependencies.
"""

from __future__ import annotations

import re
import zlib
from pathlib import Path

from services.normalizer import VENDOR_ALIASES

STREAM_PATTERN = re.compile(
    rb"<<(?P<header>.*?)>>\s*stream\r?\n(?P<body>.*?)\r?\nendstream",
    re.S,
)
TEXT_OPERATION_PATTERN = re.compile(
    r"(\[(?:.|\n)*?\]\s*TJ|\((?:\\.|[^\\()])*\)\s*Tj)",
    re.S,
)
STRING_PATTERN = re.compile(r"\((?:\\.|[^\\()])*\)")
MONEY_PATTERN = re.compile(r"\$[0-9][0-9,]*\.\d{2}")


def _clean_text(value: str) -> str:
    text = str(value).lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _canonicalize_vendor(value: str | None) -> str | None:
    if not value:
        return None

    normalized = _clean_text(value)
    if not normalized:
        return None

    for alias_key, alias_value in VENDOR_ALIASES.items():
        if alias_key in normalized:
            return alias_value

    return normalized.replace(" ", "_")


def _decode_pdf_literal(value: str) -> str:
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]

    chars: list[str] = []
    idx = 0
    while idx < len(value):
        char = value[idx]
        if char != "\\":
            chars.append(char)
            idx += 1
            continue

        idx += 1
        if idx >= len(value):
            break

        escaped = value[idx]
        mapping = {
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "b": "\b",
            "f": "\f",
            "(": "(",
            ")": ")",
            "\\": "\\",
        }
        chars.append(mapping.get(escaped, escaped))
        idx += 1

    return "".join(chars)


def _extract_stream_payloads(pdf_bytes: bytes) -> list[bytes]:
    payloads: list[bytes] = []
    for match in STREAM_PATTERN.finditer(pdf_bytes):
        header = match.group("header")
        body = match.group("body").strip(b"\r\n")
        if b"/FlateDecode" in header:
            try:
                payloads.append(zlib.decompress(body))
                continue
            except zlib.error:
                pass
        payloads.append(body)
    return payloads


def extract_pdf_text(pdf_path: Path) -> list[str]:
    pdf_bytes = pdf_path.read_bytes()
    fragments: list[str] = []

    for stream in _extract_stream_payloads(pdf_bytes):
        stream_text = stream.decode("latin-1", "ignore")
        for operation in TEXT_OPERATION_PATTERN.finditer(stream_text):
            token = operation.group(1)
            if token.endswith("Tj"):
                literal = token.rsplit(")", 1)[0] + ")"
                fragments.append(_decode_pdf_literal(literal).strip())
                continue

            for literal in STRING_PATTERN.findall(token):
                decoded = _decode_pdf_literal(literal).strip()
                if decoded:
                    fragments.append(decoded)

    return [fragment for fragment in fragments if fragment]


def _find_value_after_labels(lines: list[str], labels: list[str], max_distance: int = 2) -> str | None:
    wanted = [label.lower() for label in labels]
    for index, line in enumerate(lines):
        lower = line.lower()
        if not any(lower.startswith(label) for label in wanted):
            continue

        if ":" in line:
            value = line.split(":", 1)[1].strip()
            if value:
                return value

        for offset in range(1, max_distance + 1):
            next_index = index + offset
            if next_index >= len(lines):
                break
            candidate = lines[next_index].strip()
            if candidate:
                return candidate
    return None


def _parse_money(value: str | None) -> float | None:
    if not value:
        return None

    match = MONEY_PATTERN.search(value)
    if not match:
        return None

    return round(float(match.group(0).replace("$", "").replace(",", "")), 2)


def _collect_currency_between_markers(
    lines: list[str],
    start_labels: list[str],
    end_labels: list[str],
) -> list[float]:
    start_index: int | None = None
    end_index = len(lines)

    wanted_start = [label.lower() for label in start_labels]
    wanted_end = [label.lower() for label in end_labels]

    for index, line in enumerate(lines):
        lower = line.lower()
        if start_index is None and any(lower.startswith(label) for label in wanted_start):
            start_index = index + 1
            continue

        if start_index is not None and any(lower.startswith(label) for label in wanted_end):
            end_index = index
            break

    if start_index is None:
        return []

    values: list[float] = []
    for line in lines[start_index:end_index]:
        amount = _parse_money(line)
        if amount is not None:
            values.append(amount)
    return values


def _detect_document_type(lines: list[str]) -> str:
    joined = " ".join(lines[:24]).lower()
    if "supplier invoice" in joined or "invoice #" in joined:
        return "invoice"
    if "fleet card fuel receipt" in joined or "receipt notes" in joined:
        return "fuel_receipt"
    if "statement" in joined or "billing period" in joined:
        return "utility_statement"
    return "unknown"


def parse_supporting_document(pdf_path: Path) -> dict:
    lines = extract_pdf_text(pdf_path)
    document_type = _detect_document_type(lines)
    issuer = lines[0] if lines else pdf_path.stem

    total_amount = _parse_money(
        _find_value_after_labels(lines, ["Amount Due", "Total Due", "Total Paid"], max_distance=3)
    )
    subtotal_amount = _parse_money(_find_value_after_labels(lines, ["Subtotal"]))
    tax_amount = _parse_money(_find_value_after_labels(lines, ["HST", "GST", "Tax"]))

    line_item_amounts: list[float] = []
    if subtotal_amount is None:
        line_item_amounts = _collect_currency_between_markers(
            lines,
            start_labels=["Charge Description", "Charge Detail"],
            end_labels=["Total Due", "Amount Due", "Total Paid", "Payment Notes", "Receipt Notes"],
        )

    math_delta: float | None = None
    if total_amount is not None and subtotal_amount is not None and tax_amount is not None:
        math_delta = round(total_amount - (subtotal_amount + tax_amount), 2)
    elif total_amount is not None and line_item_amounts:
        math_delta = round(total_amount - sum(line_item_amounts), 2)

    parser_notes: list[str] = []
    if total_amount is None:
        parser_notes.append("Unable to identify a document total automatically.")
    if document_type == "unknown":
        parser_notes.append("Document layout was not recognized; review manually.")

    return {
        "fileName": pdf_path.name,
        "documentType": document_type,
        "issuer": issuer,
        "canonicalVendor": _canonicalize_vendor(issuer),
        "issueDate": _find_value_after_labels(lines, ["Statement Date", "Issue Date", "Date"]),
        "dueDate": _find_value_after_labels(lines, ["Payment Due", "Due Date"]),
        "billingPeriod": _find_value_after_labels(lines, ["Billing Period"]),
        "referenceId": _find_value_after_labels(
            lines,
            ["Invoice #", "Account Number", "Merchant ID", "Card Ref"],
        ),
        "totalAmount": total_amount,
        "subtotalAmount": subtotal_amount,
        "taxAmount": tax_amount,
        "lineItemAmounts": line_item_amounts,
        "mathDelta": math_delta,
        "parserNotes": parser_notes,
        "rawTextPreview": " ".join(lines[:18])[:320],
    }


def parse_supporting_documents(upload_dir: Path) -> list[dict]:
    documents: list[dict] = []
    for pdf_path in sorted(upload_dir.glob("*.pdf")):
        document = parse_supporting_document(pdf_path)
        documents.append(document)
    return documents
