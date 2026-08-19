"""
Streamlit UI — Pricing Intelligence Agent

Run with:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ── path setup so analysis/ imports resolve when running from any directory ───
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from analysis.elasticity import fit_all_elasticities, get_elasticity
from analysis.recommend import get_recommendation
from analysis.llm_reasoning import generate_justification

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pricing Intelligence Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS — clean, minimal, dark-friendly ────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
    }
    .metric-label { color: #94a3b8; font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }
    .metric-value { color: #f1f5f9; font-size: 1.6rem; font-weight: 700; margin-top: 0.15rem; }

    .callout-raise  { background: #052e16; border-left: 4px solid #22c55e; border-radius: 8px; padding: 1rem 1.25rem; }
    .callout-lower  { background: #450a0a; border-left: 4px solid #ef4444; border-radius: 8px; padding: 1rem 1.25rem; }
    .callout-hold   { background: #0c1a3a; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 1rem 1.25rem; }
    .callout-title  { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.4rem; }
    .callout-body   { font-size: 0.95rem; color: #cbd5e1; }

    .justification-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        font-size: 0.97rem;
        line-height: 1.65;
        color: #e2e8f0;
        margin-top: 0.75rem;
    }

    div[data-testid="stSidebar"] { background: #0f172a; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading pricing data …")
def load_data() -> pd.DataFrame:
    data_path = _ROOT / "data" / "pricing_data.csv"
    if not data_path.exists():
        st.error(
            "pricing_data.csv not found. "
            "Run `python data/generate_data.py` first."
        )
        st.stop()
    return pd.read_csv(data_path)


@st.cache_data(show_spinner="Fitting elasticity models …")
def load_elasticities(_df: pd.DataFrame) -> dict[str, float]:
    return fit_all_elasticities(_df)


df = load_data()
elasticities = load_elasticities(df)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Pricing Intelligence")
    st.markdown("---")

    categories = sorted(df["category"].unique())
    selected_category = st.selectbox("**Category**", categories)

    skus_in_cat = sorted(
        df[df["category"] == selected_category]["sku_id"].unique()
    )
    selected_sku = st.selectbox("**SKU**", skus_in_cat)

    st.markdown("---")
    st.markdown(
        "<small style='color:#64748b'>Powered by log-log OLS elasticity + Groq LLaMA 3.1</small>",
        unsafe_allow_html=True,
    )

# ── about expander ────────────────────────────────────────────────────────────
with st.expander("ℹ️ About this project", expanded=False):
    st.markdown(
        """
**Pricing Intelligence Agent** automates the work of a Data Analyst — Pricing role.
It ingests a product's price history, fits a price-elasticity model per category,
and generates an evidence-based price recommendation — then asks an LLM to write
the business justification a pricing analyst would present to a revenue manager.

**Use case:** Revenue teams at e-commerce and B2B SaaS companies use tools like this
to identify pricing leakage (money left on the table) and over-pricing risk (volume loss),
enabling data-driven repricing at scale instead of ad-hoc gut feel.
        """
    )

# ── main panel ────────────────────────────────────────────────────────────────
st.markdown(f"## 📦 SKU: `{selected_sku}`")
st.markdown(f"**Category:** {selected_category}")
st.markdown("---")

# compute recommendation
rec = get_recommendation(selected_sku, df)

# ── metric row ────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

def metric_card(label: str, value: str) -> str:
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'</div>'
    )

with col1:
    st.markdown(metric_card("Current Price", f"${rec['current_price']:.2f}"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("Competitor Price", f"${rec['competitor_price']:.2f}"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("Gross Margin", f"{rec['margin']:.1f}%"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("Elasticity (est.)", f"{rec['elasticity']:.3f}"), unsafe_allow_html=True)

st.markdown("---")

# ── price and units charts ────────────────────────────────────────────────────
sku_history = df[df["sku_id"] == selected_sku].sort_values("week").reset_index(drop=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**📈 Price History (Your Price vs Competitor)**")
    price_chart_df = sku_history[["week", "your_price", "competitor_price"]].set_index("week")
    st.line_chart(price_chart_df, color=["#3b82f6", "#f59e0b"], height=220)

with chart_col2:
    st.markdown("**📦 Weekly Units Sold**")
    units_chart_df = sku_history[["week", "units_sold"]].set_index("week")
    st.line_chart(units_chart_df, color=["#22c55e"], height=220)

st.markdown("---")

# ── recommendation callout ────────────────────────────────────────────────────
direction = rec["direction"]
direction_colors = {"raise": "raise", "lower": "lower", "hold": "hold"}
direction_icons  = {"raise": "⬆️", "lower": "⬇️", "hold": "➡️"}
direction_labels = {"raise": "RAISE PRICE", "lower": "LOWER PRICE", "hold": "HOLD PRICE"}

callout_class = f"callout-{direction_colors[direction]}"
icon = direction_icons[direction]
label = direction_labels[direction]

gap_sign = "below" if rec["competitor_gap"] < 0 else "above"

callout_html = f"""
<div class="{callout_class}">
  <div class="callout-title">{icon} Recommendation: {label}</div>
  <div class="callout-body">
    <strong>Suggested price:</strong> ${rec['suggested_price']:.2f}
    &nbsp;|&nbsp;
    <strong>Change:</strong> {'+' if direction == 'raise' else '-' if direction == 'lower' else ''}{rec['change_pct']:.2f}%
    &nbsp;|&nbsp;
    <strong>Competitor gap:</strong> {abs(rec['competitor_gap']):.1f}% {gap_sign} market
    &nbsp;|&nbsp;
    <strong>Post-adjustment margin:</strong> {((rec['suggested_price'] - rec['cost']) / rec['suggested_price'] * 100):.1f}%
  </div>
</div>
"""
st.markdown(callout_html, unsafe_allow_html=True)

st.markdown(" ")

# ── AI justification ──────────────────────────────────────────────────────────
st.markdown("### 🤖 AI Justification")

if st.button("✨ Generate AI Justification", type="primary"):
    with st.spinner("Asking the pricing analyst AI …"):
        justification = generate_justification(rec)
    st.markdown(
        f'<div class="justification-card">{justification}</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── raw data expander ─────────────────────────────────────────────────────────
with st.expander("🗂️ Raw SKU Data (last 10 weeks)"):
    st.dataframe(
        sku_history.tail(10)[
            ["week", "your_price", "competitor_price", "cost", "units_sold"]
        ].reset_index(drop=True),
        width='stretch',
    )

with st.expander("📊 Category Elasticity Summary"):
    elast_df = pd.DataFrame(
        [
            {"Category": cat, "Elasticity": round(e, 4)}
            for cat, e in elasticities.items()
        ]
    ).sort_values("Elasticity")
    st.dataframe(elast_df, width='stretch', hide_index=True)
