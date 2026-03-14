"""
CSV parser — reads and validates the uploaded QuickBooks CSV.
"""

from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = {"date", "category", "description", "amount", "vendor"}


def parse_csv(csv_path: Path) -> pd.DataFrame:
    """
    Read the CSV, validate required columns, and return a cleaned DataFrame.
    """
    df = pd.read_csv(csv_path)

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    # Clean amount — remove $, commas, negatives, cast to float
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(r"[\$,\(\)]", "", regex=True)
        .str.strip()
        .astype(float)
        .abs()
    )

    # Drop rows with zero or NaN amount
    df = df[df["amount"] > 0].copy()

    return df
