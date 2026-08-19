"""
Elasticity estimation module.

Fits log(units_sold) ~ log(your_price) per category using OLS (statsmodels).
Exposes get_elasticity(category) -> float and fit_all_elasticities() -> dict.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

# ── path helpers ──────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_DATA_PATH = _ROOT / "data" / "pricing_data.csv"

# module-level cache so we don't refit on every call
_ELASTICITY_CACHE: dict[str, float] = {}
_R2_CACHE: dict[str, float] = {}


def fit_all_elasticities(df: pd.DataFrame | None = None) -> dict[str, float]:
    """
    Fit a within-SKU log-log OLS model per category and cache results.

    We demean log(price) and log(units_sold) per SKU first (fixed-effects
    approach) so that between-SKU heterogeneity in base price / base demand
    does not confound the elasticity estimate.  Within each SKU the only
    variation left is the week-to-week price drift (±5%), which is exactly
    the signal we baked in during data generation.

    Returns:
        {category: elasticity_coefficient}
    """
    global _ELASTICITY_CACHE, _R2_CACHE

    if df is None:
        df = pd.read_csv(_DATA_PATH)

    elasticities: dict[str, float] = {}
    r2_values: dict[str, float] = {}

    print("\n" + "=" * 55)
    print("  Log-Log OLS Elasticity Fit (within-SKU) per Category")
    print("=" * 55)
    print(f"  {'Category':<20} {'Elasticity':>12} {'R2':>8}")
    print("  " + "-" * 42)

    for cat, grp in df.groupby("category"):
        # safety filter
        grp = grp[(grp["your_price"] > 0) & (grp["units_sold"] > 0)].copy()

        # ── within-SKU demeaning ────────────────────────────────────────────
        grp["log_price"] = np.log(grp["your_price"])
        grp["log_units"] = np.log(grp["units_sold"])

        # SKU-level means
        sku_means = grp.groupby("sku_id")[["log_price", "log_units"]].transform("mean")
        grp["dm_log_price"] = grp["log_price"] - sku_means["log_price"]
        grp["dm_log_units"] = grp["log_units"] - sku_means["log_units"]

        X = sm.add_constant(grp["dm_log_price"].values)
        y = grp["dm_log_units"].values

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.OLS(y, X).fit()

        coef = float(model.params[1])  # slope = elasticity
        r2 = float(model.rsquared)

        elasticities[str(cat)] = coef
        r2_values[str(cat)] = r2
        print(f"  {cat:<20} {coef:>12.4f} {r2:>8.4f}")

    print("=" * 55)

    _ELASTICITY_CACHE = elasticities
    _R2_CACHE = r2_values
    return elasticities


def get_elasticity(category: str, df: pd.DataFrame | None = None) -> float:
    """
    Return the estimated price elasticity for a given category.
    Fits models if not yet cached.
    """
    if not _ELASTICITY_CACHE:
        fit_all_elasticities(df)
    if category not in _ELASTICITY_CACHE:
        raise ValueError(
            f"Category '{category}' not found. "
            f"Available: {list(_ELASTICITY_CACHE.keys())}"
        )
    return _ELASTICITY_CACHE[category]


def get_r2(category: str) -> float:
    """Return the R² for a fitted category model."""
    if not _R2_CACHE:
        fit_all_elasticities()
    return _R2_CACHE.get(category, float("nan"))


if __name__ == "__main__":
    elasticities = fit_all_elasticities()
    print("\nFitted elasticities:")
    for cat, e in elasticities.items():
        print(f"  {cat}: {e:.4f}  (R²={get_r2(cat):.4f})")
