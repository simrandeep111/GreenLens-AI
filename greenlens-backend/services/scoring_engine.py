"""
Deterministic ESG scoring engine.
No LLM involvement — all scores are computed from formulas.
"""

from core.config import SECTOR_AVERAGES, SECTOR_TOP_QUARTILE

# ── Social/Governance scoring grids ────────────────────────────────────
# Each question max 5 pts.  Answer text → points.
QUESTION_SCORES: dict[str, dict[str, int]] = {
    "Yes":          5,
    "In Progress":  3,
    "Partial":      2,
    "Planned":      2,
    "No":           0,
}


def _parse_revenue(revenue_str: str) -> float:
    """Convert '$2,400,000' → 2400000.0"""
    cleaned = revenue_str.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def calculate_environmental_score(
    total_tCO2e: float,
    revenue_str: str,
    industry: str,
) -> tuple[int, float, float, float]:
    """
    Returns: (score_out_of_50, intensity, sector_avg, top_quartile)
    """
    revenue = _parse_revenue(revenue_str)
    if revenue <= 0:
        return (0, 0.0, 0.0, 0.0)

    intensity = (total_tCO2e * 1000) / (revenue / 1000)  # kgCO2e per $1k revenue
    sector_avg = SECTOR_AVERAGES.get(industry, 80.0)
    top_q = SECTOR_TOP_QUARTILE.get(industry, 50.0)
    ratio = intensity / sector_avg

    if ratio <= 0.50:   score = 50
    elif ratio <= 0.75: score = 42
    elif ratio <= 1.00: score = 34
    elif ratio <= 1.25: score = 22
    elif ratio <= 1.50: score = 12
    else:               score = 4

    return (score, round(intensity, 1), sector_avg, top_q)


def calculate_social_score(answers: list[str]) -> int:
    """
    First 2 governance_answers are treated as Social questions.
    Max 25 pts: 5 base + up to 5 pts per answer (max 4 answers contributing).
    For the demo we use the first 2 answers as social, last 2 as governance.
    """
    base = 5
    pts = sum(QUESTION_SCORES.get(a, 0) for a in answers[:2])
    return min(25, base + pts)


def calculate_governance_score(answers: list[str]) -> int:
    """Last 2 governance_answers are Governance questions."""
    base = 5
    pts = sum(QUESTION_SCORES.get(a, 0) for a in answers[2:4])
    return min(25, base + pts)


def score_grade(total: int) -> str:
    if total >= 80:
        return "Leading"
    if total >= 65:
        return "Advanced"
    if total >= 50:
        return "Developing"
    return "Emerging"


def calculate_full_score(
    total_tCO2e: float,
    revenue_str: str,
    industry: str,
    governance_answers: list[str],
) -> dict:
    """
    Run the complete scoring pipeline.
    Returns the score dict + benchmark info.
    """
    e_score, intensity, sector_avg, top_q = calculate_environmental_score(
        total_tCO2e, revenue_str, industry,
    )
    s_score = calculate_social_score(governance_answers)
    g_score = calculate_governance_score(governance_answers)
    total = e_score + s_score + g_score
    grade = score_grade(total)

    return {
        "score": {
            "total": total,
            "environmental": e_score,
            "social": s_score,
            "governance": g_score,
            "grade": grade,
        },
        "benchmark": {
            "yourIntensity": intensity,
            "sectorAverage": sector_avg,
            "topQuartile": top_q,
        },
    }
