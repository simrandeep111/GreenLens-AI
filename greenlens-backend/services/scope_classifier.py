"""
Hybrid scope classifier — 3 layers:
  1. Known vendor dictionary
  2. Keyword/rule engine
  3. Default fallback (Scope 3)
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import pandas as pd


# ── Layer 1: canonical vendor → scope mapping ──────────────────────────
VENDOR_SCOPE = {
    # (scope, sub_category, confidence)
    "enbridge_gas":     ("Scope 1", "natural_gas",  0.98),
    "shell_fuel":       ("Scope 1", "gasoline",     0.95),
    "petro_canada":     ("Scope 1", "gasoline",     0.95),
    "esso_fuel":        ("Scope 1", "gasoline",     0.95),
    "pioneer_fuel":     ("Scope 1", "diesel",       0.93),
    "toronto_hydro":    ("Scope 2", "electricity",  0.98),
    "hydro_one":        ("Scope 2", "electricity",  0.98),
    "hydro_ottawa":     ("Scope 2", "electricity",  0.98),
    "air_canada":       ("Scope 3", "travel",       0.95),
    "westjet":          ("Scope 3", "travel",       0.95),
    "uber":             ("Scope 3", "travel",       0.90),
    "lyft":             ("Scope 3", "travel",       0.90),
    "sysco_food":       ("Scope 3", "food_supply",  0.95),
    "gordon_food":      ("Scope 3", "food_supply",  0.95),
    "waste_mgmt":       ("Scope 3", "waste",        0.95),
    "waste_connections":("Scope 3", "waste",        0.95),
    "purolator":        ("Scope 3", "shipping",     0.92),
    "canada_post":      ("Scope 3", "shipping",     0.90),
    "fedex":            ("Scope 3", "shipping",     0.92),
    "ups":              ("Scope 3", "shipping",     0.92),
    "staples":          ("Scope 3", "office_supplies", 0.88),
    "grand_toy":        ("Scope 3", "office_supplies", 0.88),
}

# ── Layer 2: keyword rules ─────────────────────────────────────────────
SCOPE1_KEYWORDS = [
    "natural gas", "propane", "diesel", "gasoline", "fuel",
    "fleet", "combustion", "heating oil", "furnace",
]
SCOPE2_KEYWORDS = [
    "hydro", "electricity", "electric", "power bill",
    "utility power", "kwh",
]
SCOPE3_SUBCATEGORY_KEYWORDS = {
    "travel":       ["air", "flight", "hotel", "travel", "taxi", "rideshare", "uber", "lyft"],
    "shipping":     ["shipping", "freight", "courier", "delivery", "postage"],
    "food_supply":  ["food", "catering", "produce", "grocery", "ingredients", "meat", "dairy"],
    "waste":        ["waste", "disposal", "recycling", "compost", "landfill"],
    "packaging":    ["packaging", "container", "box", "wrap"],
    "professional_services": ["consulting", "legal", "accounting", "professional", "advisory"],
    "office_supplies": ["office", "supplies", "paper", "toner", "stationery"],
}


def _match_keywords(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def _detect_scope3_subcategory(text: str) -> str:
    for subcat, kws in SCOPE3_SUBCATEGORY_KEYWORDS.items():
        if _match_keywords(text, kws):
            return subcat
    return "general_scope3"


def classify_row(row: pd.Series) -> dict:
    """
    Classify a single normalised row into scope + subcategory.
    Returns dict with: scope, subcategory, confidence, reason, source
    """
    canonical = row.get("canonical_vendor")

    # ── Layer 1: vendor dictionary ──
    if canonical and canonical in VENDOR_SCOPE:
        scope, subcat, conf = VENDOR_SCOPE[canonical]
        return {
            "scope": scope,
            "subcategory": subcat,
            "confidence": conf,
            "reason": f"Vendor dictionary: {canonical} → {scope} ({subcat})",
            "source": "vendor_dict",
        }

    # Combine text for keyword matching
    combined = f"{row['norm_vendor']} {row['norm_category']} {row['norm_description']}"

    # ── Layer 2: keyword rules ──
    if _match_keywords(combined, SCOPE1_KEYWORDS):
        return {
            "scope": "Scope 1",
            "subcategory": "natural_gas" if "gas" in combined else "gasoline",
            "confidence": 0.82,
            "reason": f"Keyword match → Scope 1 in: {combined[:60]}",
            "source": "keyword_rule",
        }

    if _match_keywords(combined, SCOPE2_KEYWORDS):
        return {
            "scope": "Scope 2",
            "subcategory": "electricity",
            "confidence": 0.85,
            "reason": f"Keyword match → Scope 2 in: {combined[:60]}",
            "source": "keyword_rule",
        }

    # ── Layer 3: default Scope 3 with subcategory detection ──
    subcat = _detect_scope3_subcategory(combined)
    return {
        "scope": "Scope 3",
        "subcategory": subcat,
        "confidence": 0.70,
        "reason": f"Default Scope 3 ({subcat}) — no strong Scope 1/2 signal in: {combined[:60]}",
        "source": "default_rule",
    }


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Classify all rows, adding scope/subcategory/confidence columns."""
    results = df.apply(classify_row, axis=1, result_type="expand")
    return pd.concat([df, results], axis=1)
