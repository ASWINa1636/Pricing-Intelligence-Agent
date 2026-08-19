"""
Unit tests for the Pricing Intelligence Agent recommendation engine.

Run with:
    pytest tests/test_recommend.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ensure project root is on path so imports resolve
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pricing_df() -> pd.DataFrame:
    """Load (or generate) the pricing dataset once per test session."""
    data_path = _ROOT / "data" / "pricing_data.csv"
    if not data_path.exists():
        # Generate on-the-fly so tests are self-contained
        from data.generate_data import generate_dataset
        df = generate_dataset()
        data_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(data_path, index=False)
    return pd.read_csv(data_path)


@pytest.fixture(scope="module")
def sample_skus(pricing_df: pd.DataFrame):
    """Return 20 diverse SKU ids for testing."""
    return pricing_df["sku_id"].drop_duplicates().sample(20, random_state=99).tolist()


@pytest.fixture(scope="module")
def sample_recommendations(pricing_df: pd.DataFrame, sample_skus):
    """Pre-compute recommendations for all sample SKUs."""
    from analysis.recommend import get_recommendation
    return [get_recommendation(sku, pricing_df) for sku in sample_skus]


# ── test 1: required keys ─────────────────────────────────────────────────────

REQUIRED_KEYS = {
    "sku_id",
    "category",
    "current_price",
    "competitor_price",
    "cost",
    "elasticity",
    "competitor_gap",
    "margin",
    "suggested_price",
    "direction",
    "change_pct",
}


def test_recommendation_has_all_required_keys(sample_recommendations):
    """get_recommendation() must return all required keys."""
    for rec in sample_recommendations:
        missing = REQUIRED_KEYS - set(rec.keys())
        assert not missing, (
            f"SKU {rec.get('sku_id')} recommendation is missing keys: {missing}"
        )


# ── test 2: margin floor ──────────────────────────────────────────────────────

MARGIN_FLOOR = 0.10  # 10 %


def test_suggested_price_never_violates_margin_floor(sample_recommendations):
    """Suggested price must always yield >= 10 % gross margin."""
    for rec in sample_recommendations:
        cost = rec["cost"]
        suggested = rec["suggested_price"]
        if suggested > 0:
            margin = (suggested - cost) / suggested
            assert margin >= MARGIN_FLOOR - 1e-6, (
                f"SKU {rec['sku_id']}: suggested_price ${suggested:.2f} yields "
                f"margin {margin*100:.2f}% — below the {MARGIN_FLOOR*100:.0f}% floor. "
                f"cost=${cost:.2f}"
            )


# ── test 3: elasticity sign sanity ────────────────────────────────────────────

def test_all_category_elasticities_are_negative():
    """
    Fitted elasticity coefficients must be negative for all categories —
    a basic economic sanity check (higher price → lower demand).
    """
    from analysis.elasticity import fit_all_elasticities
    # Pass None so it reads from file
    elasticities = fit_all_elasticities()
    for cat, e in elasticities.items():
        assert e < 0, (
            f"Category '{cat}' has positive elasticity {e:.4f} — "
            "unexpected for a normal good."
        )


# ── test 4: direction validity ────────────────────────────────────────────────

def test_direction_is_valid_enum(sample_recommendations):
    """direction must be one of 'raise', 'lower', 'hold'."""
    valid = {"raise", "lower", "hold"}
    for rec in sample_recommendations:
        assert rec["direction"] in valid, (
            f"SKU {rec['sku_id']}: invalid direction '{rec['direction']}'"
        )


# ── test 5: numeric types and value ranges ────────────────────────────────────

def test_prices_are_positive(sample_recommendations):
    """current_price, competitor_price, cost, suggested_price must all be > 0."""
    for rec in sample_recommendations:
        for field in ("current_price", "competitor_price", "cost", "suggested_price"):
            assert rec[field] > 0, (
                f"SKU {rec['sku_id']}: {field}={rec[field]} is not positive."
            )


def test_change_pct_is_non_negative(sample_recommendations):
    """change_pct must be non-negative (direction encodes the sign)."""
    for rec in sample_recommendations:
        assert rec["change_pct"] >= 0, (
            f"SKU {rec['sku_id']}: change_pct={rec['change_pct']} is negative."
        )


# ── test 6: hold direction leaves price unchanged ─────────────────────────────

def test_hold_direction_keeps_price_unchanged(sample_recommendations):
    """When direction=='hold', suggested_price must equal current_price."""
    for rec in sample_recommendations:
        if rec["direction"] == "hold":
            assert abs(rec["suggested_price"] - rec["current_price"]) < 0.01, (
                f"SKU {rec['sku_id']}: direction=hold but price changed "
                f"{rec['current_price']} → {rec['suggested_price']}"
            )
