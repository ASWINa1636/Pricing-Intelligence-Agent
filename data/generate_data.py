"""
Synthetic dataset generator for the Pricing Intelligence Agent.

Generates 800 SKUs × 26 weeks = 20,800 rows with realistic elasticity behaviour
baked in per category.  Run directly to (re)generate data/pricing_data.csv.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# ── reproducibility ──────────────────────────────────────────────────────────
SEED = 42
rng = np.random.default_rng(SEED)

# ── configuration ─────────────────────────────────────────────────────────────
N_SKUS = 800
N_WEEKS = 26          # 6 months of weekly data
CATEGORIES = [
    "Electronics",
    "Home Appliances",
    "Accessories",
    "Networking",
    "Storage",
    "Peripherals",
]

# True elasticity per category (negative; drawn once, fixed for reproducibility)
# Range: -0.2 (inelastic) to -1.8 (elastic)
CATEGORY_ELASTICITY = {
    "Electronics":      -1.50,
    "Home Appliances":  -0.90,
    "Accessories":      -1.70,
    "Networking":       -0.35,
    "Storage":          -1.20,
    "Peripherals":      -0.60,
}

# Base demand per category (average units per week at base price)
CATEGORY_BASE_DEMAND = {
    "Electronics":     50,
    "Home Appliances": 20,
    "Accessories":    200,
    "Networking":      40,
    "Storage":         80,
    "Peripherals":    120,
}

# Typical base price ranges per category (USD)
CATEGORY_PRICE_RANGE = {
    "Electronics":     (80,  600),
    "Home Appliances": (100, 800),
    "Accessories":     (10,   80),
    "Networking":      (30,  250),
    "Storage":         (20,  150),
    "Peripherals":     (15,  120),
}


def generate_dataset() -> pd.DataFrame:
    records = []
    skus_per_cat = N_SKUS // len(CATEGORIES)

    for cat in CATEGORIES:
        elasticity = CATEGORY_ELASTICITY[cat]
        base_demand = CATEGORY_BASE_DEMAND[cat]
        price_lo, price_hi = CATEGORY_PRICE_RANGE[cat]

        for s in range(skus_per_cat):
            sku_id = f"{cat[:3].upper()}_{s+1:04d}"

            # Base price for this SKU — fixed anchor, varies by SKU
            base_price = rng.uniform(price_lo, price_hi)

            # cost is fixed per SKU: 55–80 % of base price
            cost_pct = rng.uniform(0.55, 0.80)
            cost = round(base_price * cost_pct, 2)

            for week in range(N_WEEKS):
                # Weekly price drift ±5 % around the base price
                drift = rng.uniform(-0.05, 0.05)
                your_price = round(base_price * (1 + drift), 2)

                # Competitor price: your_price × factor in [0.85, 1.15]
                comp_factor = rng.uniform(0.85, 1.15)
                competitor_price = round(your_price * comp_factor, 2)

                # Demand: log-log model with log-normal noise (σ = 0.08)
                noise = rng.lognormal(mean=0.0, sigma=0.08)
                units_sold = max(
                    1,
                    int(
                        base_demand
                        * (your_price / base_price) ** elasticity
                        * noise
                    ),
                )

                records.append(
                    {
                        "sku_id": sku_id,
                        "category": cat,
                        "week": week + 1,
                        "your_price": your_price,
                        "competitor_price": competitor_price,
                        "cost": cost,
                        "units_sold": units_sold,
                    }
                )

    df = pd.DataFrame(records)
    return df


def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("  Pricing Data — Summary Statistics")
    print("=" * 60)
    print(f"  Total rows    : {len(df):,}")
    print(f"  Unique SKUs   : {df['sku_id'].nunique():,}")
    print(f"  Weeks         : {df['week'].min()} – {df['week'].max()}")
    print(f"  Categories    : {sorted(df['category'].unique())}")
    print()
    grp = df.groupby("category").agg(
        skus=("sku_id", "nunique"),
        avg_price=("your_price", "mean"),
        avg_units=("units_sold", "mean"),
        true_elasticity=("category", lambda s: CATEGORY_ELASTICITY[s.iloc[0]]),
    )
    print(grp.round(2).to_string())
    print("=" * 60)


if __name__ == "__main__":
    out_path = Path(__file__).parent / "pricing_data.csv"
    print("Generating synthetic pricing data ...")
    df = generate_dataset()
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df):,} rows -> {out_path}")
    print_summary(df)
