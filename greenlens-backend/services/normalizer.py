"""
Normalizer — cleans and standardises vendor/category/description text.
"""

import re
import pandas as pd


# Known vendor aliases → canonical vendor name
VENDOR_ALIASES: dict[str, str] = {
    "enbridge gas":       "enbridge_gas",
    "enbridge":           "enbridge_gas",
    "union gas":          "enbridge_gas",
    "toronto hydro":      "toronto_hydro",
    "hydro one":          "hydro_one",
    "hydro ottawa":       "hydro_ottawa",
    "shell":              "shell_fuel",
    "shell canada":       "shell_fuel",
    "petro-canada":       "petro_canada",
    "petro canada":       "petro_canada",
    "esso":               "esso_fuel",
    "pioneer energy":     "pioneer_fuel",
    "air canada":         "air_canada",
    "westjet":            "westjet",
    "uber":               "uber",
    "uber for business":  "uber",
    "lyft":               "lyft",
    "sysco":              "sysco_food",
    "sysco food":         "sysco_food",
    "gordon food":        "gordon_food",
    "gfs":                "gordon_food",
    "waste management":   "waste_mgmt",
    "waste connections":  "waste_connections",
    "purolator":          "purolator",
    "canada post":        "canada_post",
    "fedex":              "fedex",
    "ups":                "ups",
    "staples":            "staples",
    "grand & toy":        "grand_toy",
}


def _clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add normalised columns: norm_vendor, norm_category, norm_description, canonical_vendor.
    """
    df = df.copy()

    df["norm_vendor"]      = df["vendor"].apply(_clean_text)
    df["norm_category"]    = df["category"].apply(_clean_text)
    df["norm_description"] = df["description"].apply(_clean_text)

    # Canonical vendor lookup
    df["canonical_vendor"] = df["norm_vendor"].map(
        lambda v: next(
            (alias for key, alias in VENDOR_ALIASES.items() if key in v),
            None,
        )
    )

    return df
