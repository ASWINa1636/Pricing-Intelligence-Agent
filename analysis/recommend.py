"""
Recommendation engine for Pricing Intelligence Agent.

Core function: get_recommendation(sku_id, df) -> dict
Decision logic:
  - Inelastic (|e| < 0.6) & at/below market → raise price
  - Elastic   (|e| ≥ 1.2) & notably above market → lower price
  - Otherwise → hold
Margin floor: recommended price must yield ≥ 10 % margin.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from analysis.elasticity import get_elasticity, fit_all_elasticities

# ── constants ─────────────────────────────────────────────────────────────────
MARGIN_FLOOR = 0.10          # never drop below 10 % margin
INELASTIC_THRESHOLD = 0.6    # |elasticity| < this → inelastic
ELASTIC_THRESHOLD = 1.2      # |elasticity| ≥ this → elastic
COMP_GAP_RAISE_TRIGGER = 0.0 # at-or-below market
COMP_GAP_LOWER_TRIGGER = 0.05  # more than 5 % above market
MAX_RAISE_PCT = 0.08          # cap raise at 8 %
MAX_LOWER_PCT = 0.10          # cap lower at 10 %

_ROOT = Path(__file__).resolve().parent.parent
_DATA_PATH = _ROOT / "data" / "pricing_data.csv"


def get_recommendation(sku_id: str, df: pd.DataFrame) -> dict:
    """
    Compute a pricing recommendation for a single SKU.

    Parameters
    ----------
    sku_id : str
        SKU identifier that must exist in *df*.
    df : pd.DataFrame
        Full pricing dataset (all weeks, all SKUs).

    Returns
    -------
    dict with keys:
        sku_id, category, current_price, competitor_price,
        cost, elasticity, competitor_gap, margin,
        suggested_price, direction, change_pct
    """
    sku_df = df[df["sku_id"] == sku_id].copy()
    if sku_df.empty:
        raise ValueError(f"SKU '{sku_id}' not found in dataset.")

    # Latest week of data
    latest = sku_df.sort_values("week").iloc[-1]

    category: str = latest["category"]
    current_price: float = float(latest["your_price"])
    competitor_price: float = float(latest["competitor_price"])
    cost: float = float(latest["cost"])

    # Derived metrics
    elasticity: float = get_elasticity(category, df)
    competitor_gap: float = (current_price - competitor_price) / competitor_price
    margin: float = (current_price - cost) / current_price

    abs_e = abs(elasticity)

    # ── decision logic ──────────────────────────────────────────────────────
    direction = "hold"
    change_pct = 0.0

    if abs_e < INELASTIC_THRESHOLD and competitor_gap <= COMP_GAP_RAISE_TRIGGER:
        # Inelastic + at or below market → raise
        direction = "raise"
        change_pct = min(MAX_RAISE_PCT, abs(competitor_gap) * 0.50)
        # Ensure at least a 2 % raise when gap is ~0
        change_pct = max(change_pct, 0.02)

    elif abs_e >= ELASTIC_THRESHOLD and competitor_gap > COMP_GAP_LOWER_TRIGGER:
        # Elastic + notably above market → lower
        direction = "lower"
        change_pct = min(MAX_LOWER_PCT, competitor_gap * 0.50)

    # ── compute suggested price ──────────────────────────────────────────────
    if direction == "raise":
        suggested_price = current_price * (1 + change_pct)
    elif direction == "lower":
        suggested_price = current_price * (1 - change_pct)
    else:
        suggested_price = current_price

    # ── margin floor guard ───────────────────────────────────────────────────
    min_price = cost / (1 - MARGIN_FLOOR)
    if suggested_price < min_price:
        suggested_price = min_price
        if direction == "lower":
            # Check if we actually moved below floor and correct
            actual_change = (suggested_price - current_price) / current_price
            if actual_change >= 0:
                direction = "hold"
                change_pct = 0.0
            else:
                change_pct = abs(actual_change)

    suggested_price = round(suggested_price, 2)
    change_pct = round(change_pct * 100, 2)  # convert to percentage

    return {
        "sku_id": sku_id,
        "category": category,
        "current_price": round(current_price, 2),
        "competitor_price": round(competitor_price, 2),
        "cost": round(cost, 2),
        "elasticity": round(elasticity, 4),
        "competitor_gap": round(competitor_gap * 100, 2),   # as %
        "margin": round(margin * 100, 2),                   # as %
        "suggested_price": suggested_price,
        "direction": direction,
        "change_pct": change_pct,
    }


if __name__ == "__main__":
    import sys

    df = pd.read_csv(_DATA_PATH)
    # Pre-fit elasticities once (prints R² table)
    fit_all_elasticities(df)

    sample_skus = df["sku_id"].drop_duplicates().sample(5, random_state=42).tolist()
    print("\n" + "=" * 65)
    print("  Sample Recommendations")
    print("=" * 65)
    for sku in sample_skus:
        try:
            rec = get_recommendation(sku, df)
            print(
                f"  {rec['sku_id']:<18} [{rec['category']:<16}]  "
                f"${rec['current_price']:.2f} → ${rec['suggested_price']:.2f}  "
                f"({rec['direction'].upper():>5}, {rec['change_pct']:.2f}%)  "
                f"margin={rec['margin']:.1f}%"
            )
        except Exception as exc:
            print(f"  {sku}: ERROR — {exc}", file=sys.stderr)
    print("=" * 65)
