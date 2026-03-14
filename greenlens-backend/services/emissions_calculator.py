"""
Emissions calculator — applies emission factors to classified rows.
"""

from __future__ import annotations
import pandas as pd

from core.config import GRID_FACTORS, SPEND_FACTORS


# Average electricity price (CAD/kWh) by province — for spend→kWh conversion
ELECTRICITY_PRICES: dict[str, float] = {
    "Ontario":          0.13,
    "British Columbia": 0.12,
    "Alberta":          0.17,
    "Quebec":           0.07,
}


def _estimate_scope1_co2(amount: float, subcategory: str) -> float:
    """Spend-based estimation for Scope 1 fuels."""
    factor = SPEND_FACTORS.get(subcategory, SPEND_FACTORS.get("natural_gas", 0.05))
    return amount * factor


def _estimate_scope2_co2(amount: float, province: str) -> float:
    """Electricity: $ → kWh → kgCO2e using provincial grid factor."""
    price_per_kwh = ELECTRICITY_PRICES.get(province, 0.13)
    kwh = amount / price_per_kwh
    grid_factor_kg = GRID_FACTORS.get(province, 29.0) / 1000.0  # gCO2e → kgCO2e
    return kwh * grid_factor_kg


def _estimate_scope3_co2(amount: float, subcategory: str) -> float:
    """Spend-based estimation for Scope 3 categories."""
    factor = SPEND_FACTORS.get(subcategory, SPEND_FACTORS["general_scope3"])
    return amount * factor


def calculate_emissions(df: pd.DataFrame, province: str) -> pd.DataFrame:
    """
    Add tCO2e column to each row based on scope + subcategory + amount.
    Returns the DataFrame with `tCO2e` column.
    """
    df = df.copy()

    def _row_co2(row: pd.Series) -> float:
        scope = row["scope"]
        amount = row["amount"]
        subcat = row.get("subcategory", "general_scope3")

        if scope == "Scope 1":
            return _estimate_scope1_co2(amount, subcat)
        elif scope == "Scope 2":
            return _estimate_scope2_co2(amount, province)
        else:
            return _estimate_scope3_co2(amount, subcat)

    df["tCO2e"] = df.apply(_row_co2, axis=1)

    # Convert kg to tonnes (our factors give kgCO2e, but we report tCO2e)
    df["tCO2e"] = df["tCO2e"] / 1000.0

    return df


def aggregate_emissions(df: pd.DataFrame) -> dict:
    """
    Build the emissions summary object for the frontend.
    """
    scope1 = round(df.loc[df["scope"] == "Scope 1", "tCO2e"].sum(), 1)
    scope2 = round(df.loc[df["scope"] == "Scope 2", "tCO2e"].sum(), 1)
    scope3 = round(df.loc[df["scope"] == "Scope 3", "tCO2e"].sum(), 1)
    total = round(scope1 + scope2 + scope3, 1)

    # Breakdown by category
    breakdown_df = (
        df.groupby(["norm_category", "scope"])["tCO2e"]
        .sum()
        .reset_index()
        .rename(columns={"norm_category": "category"})
    )

    # Use original description grouping for better labels
    cat_groups = (
        df.groupby("subcategory")
        .agg({"tCO2e": "sum", "scope": "first"})
        .reset_index()
        .sort_values("tCO2e", ascending=False)
    )

    CATEGORY_LABELS = {
        "natural_gas": "Natural gas heating",
        "gasoline":    "Fleet vehicle fuel",
        "diesel":      "Fleet vehicle fuel (diesel)",
        "propane":     "Propane heating",
        "electricity": "Electricity (grid)",
        "food_supply": "Food & beverage supply chain",
        "shipping":    "Shipping & logistics",
        "waste":       "Waste disposal & packaging",
        "packaging":   "Packaging materials",
        "travel":      "Business travel & logistics",
        "office_supplies":      "Office supplies",
        "professional_services":"Professional services",
        "general_scope3":       "Other purchased goods & services",
    }

    breakdown = []
    for _, row in cat_groups.iterrows():
        t = round(row["tCO2e"], 1)
        if t <= 0:
            continue
        pct = round((t / total) * 100, 1) if total > 0 else 0
        breakdown.append({
            "category": CATEGORY_LABELS.get(row["subcategory"], row["subcategory"]),
            "scope": row["scope"],
            "tCO2e": t,
            "percentOfTotal": pct,
        })

    return {
        "totalTCO2e": total,
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
        "breakdown": breakdown,
    }
