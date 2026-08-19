"""
LLM reasoning layer for Pricing Intelligence Agent.

Uses OpenAI-compatible SDK pointed at Groq's endpoint.
Falls back to a rule-based template if GROQ_API_KEY is not set,
so the app works fully offline/demo mode.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load .env if present (no-op if python-dotenv not installed or file missing)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_GROQ_MODEL = "openai/gpt-oss-20b"

_PROMPT_TEMPLATE = (
    "You are a pricing analyst. Given elasticity of {elasticity}, "
    "competitor price gap of {competitor_gap_pct}%, and margin of {margin_pct}%, "
    "write a 2-3 sentence business justification for the recommendation to "
    "{direction} the price by {change_pct}%. "
    "Be concise and specific, referencing the actual numbers."
)

_FALLBACK_TEMPLATE = {
    "raise": (
        "With a price elasticity of {elasticity} the demand for this SKU is relatively "
        "inelastic, meaning customers are not highly sensitive to price increases. "
        "Our price is currently {competitor_gap_abs:.1f}% below the competitor benchmark, "
        "creating headroom to raise the price by {change_pct}% to ${suggested_price:.2f} "
        "while maintaining a healthy {margin_pct:.1f}% margin and capturing additional revenue."
    ),
    "lower": (
        "With a high price elasticity of {elasticity}, demand is very sensitive to price. "
        "Our price sits {competitor_gap_abs:.1f}% above the market average, "
        "likely suppressing volume. Lowering the price by {change_pct}% to "
        "${suggested_price:.2f} should stimulate demand and grow total revenue, "
        "while keeping margin above the {margin_floor:.0f}% floor."
    ),
    "hold": (
        "Current pricing is well-balanced given an elasticity of {elasticity}. "
        "The competitor gap of {competitor_gap_pct:.1f}% and margin of {margin_pct:.1f}% "
        "are within acceptable ranges, so no price adjustment is recommended at this time."
    ),
}


def _rule_based_justification(rec: dict) -> str:
    """Generate a template-based justification without calling any API."""
    direction = rec.get("direction", "hold")
    template = _FALLBACK_TEMPLATE.get(direction, _FALLBACK_TEMPLATE["hold"])
    return template.format(
        elasticity=rec.get("elasticity", "N/A"),
        competitor_gap_pct=rec.get("competitor_gap", 0.0),
        competitor_gap_abs=abs(rec.get("competitor_gap", 0.0)),
        margin_pct=rec.get("margin", 0.0),
        change_pct=rec.get("change_pct", 0.0),
        suggested_price=rec.get("suggested_price", rec.get("current_price", 0.0)),
        margin_floor=10.0,
    )


def generate_justification(recommendation: dict) -> str:
    """
    Generate a natural-language pricing justification.

    Uses Groq LLM (llama-3.1-8b-instant) when GROQ_API_KEY is set;
    otherwise falls back to a deterministic rule-based template.

    Parameters
    ----------
    recommendation : dict
        Output of recommend.get_recommendation().

    Returns
    -------
    str
        A 2-3 sentence business justification.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        return "(Demo mode — set GROQ_API_KEY for AI justification)\n\n" + \
               _rule_based_justification(recommendation)

    try:
        from openai import OpenAI  # lazy import so app loads without openai installed

        client = OpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)

        prompt = _PROMPT_TEMPLATE.format(
            elasticity=recommendation.get("elasticity", "N/A"),
            competitor_gap_pct=recommendation.get("competitor_gap", 0.0),
            margin_pct=recommendation.get("margin", 0.0),
            direction=recommendation.get("direction", "hold"),
            change_pct=recommendation.get("change_pct", 0.0),
        )

        response = client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=256,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:  # noqa: BLE001
        fallback = _rule_based_justification(recommendation)
        return f"(LLM unavailable: {exc})\n\n{fallback}"


if __name__ == "__main__":
    # Quick smoke test
    sample_rec = {
        "sku_id": "ELE_0042",
        "category": "Electronics",
        "current_price": 249.99,
        "competitor_price": 239.99,
        "cost": 149.99,
        "elasticity": -1.50,
        "competitor_gap": 4.17,
        "margin": 40.0,
        "suggested_price": 237.49,
        "direction": "lower",
        "change_pct": 5.0,
    }
    print(generate_justification(sample_rec))
