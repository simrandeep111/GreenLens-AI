"""
Core configuration — paths, Moorcheh API key, emission factors.
"""

import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

# Ensure directories exist
for d in [UPLOADS_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────
MOORCHEH_API_KEY = os.getenv("MOORCHEH_API_KEY", "")
MOORCHEH_MODEL = os.getenv("MOORCHEH_MODEL", "anthropic.claude-sonnet-4-20250514-v1:0")
MOORCHEH_BASE_URL = "https://api.moorcheh.ai/v1"

# ── Frontend CORS ─────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ── Provincial grid emission factors (gCO2e per kWh) ──────────────────
GRID_FACTORS: Dict[str, float] = {
    "Ontario":          29.0,
    "British Columbia": 12.0,
    "Alberta":         540.0,
    "Quebec":            1.7,
}

# ── Sector benchmark averages (kgCO2e per $1,000 revenue) ─────────────
SECTOR_AVERAGES: Dict[str, float] = {
    "Food & Beverage": 91.2,
    "Technology":      34.5,
    "Manufacturing":  145.8,
    "Retail":          52.3,
}

# ── Sector top-quartile (kgCO2e per $1,000 revenue) ───────────────────
SECTOR_TOP_QUARTILE: Dict[str, float] = {
    "Food & Beverage": 58.4,
    "Technology":      18.2,
    "Manufacturing":   88.5,
    "Retail":          31.0,
}

# ── Spend-based emission factors (kgCO2e per CAD $) ───────────────────
#    Calibrated for realistic Canadian SMB emissions.
#    Source: NRCan emission factors, converted via average 2024 commodity prices.
#    Natural gas: ~$0.14/m³ avg, 1.896 kgCO2e/m³ → ~13.5 kgCO2e/$
#    Diesel: ~$1.65/L, 2.68 kgCO2e/L → ~1.62 kgCO2e/$
#    Gasoline: ~$1.55/L, 2.31 kgCO2e/L → ~1.49 kgCO2e/$
SPEND_FACTORS: Dict[str, float] = {
    "natural_gas":          4.8,    # Scope 1: high factor — gas heating
    "propane":              3.5,    # Scope 1: propane heating
    "diesel":               1.6,    # Scope 1: fleet diesel
    "gasoline":             1.5,    # Scope 1: fleet gasoline
    "food_supply":          0.28,   # Scope 3: food supply chain (higher for F&B)
    "packaging":            0.45,   # Scope 3: packaging materials
    "shipping":             0.52,   # Scope 3: logistics
    "travel":               0.38,   # Scope 3: business travel (flights)
    "waste":                0.65,   # Scope 3: waste disposal and landfill
    "professional_services":0.10,   # Scope 3: professional services (low)
    "office_supplies":      0.15,   # Scope 3: office consumables
    "general_scope3":       0.20,   # Scope 3: fallback factor
}
