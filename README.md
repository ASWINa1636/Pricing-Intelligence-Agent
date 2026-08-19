# Pricing Intelligence Agent

> Automate the work of a Data Analyst — Pricing: estimate price elasticity, generate evidence-based price recommendations, and produce natural-language business justifications — all from a single Streamlit dashboard.

---

## Problem Statement

Pricing teams at e-commerce and B2B companies constantly face two opposing risks:
**pricing leakage** (revenue left on the table by under-pricing) and **volume loss**
(demand suppressed by over-pricing vs. competitors). Manual analysis is slow, inconsistent,
and doesn't scale to thousands of SKUs. This agent automates the full analyst workflow —
data → elasticity modelling → recommendation → plain-English justification — enabling
revenue managers to act on pricing insights at scale, backed by statistical evidence and
LLM-generated reasoning they can share directly with stakeholders.

---

## Architecture

```
[generate_data.py] → pricing_data.csv
        ↓
[elasticity.py] → per-category elasticity coefficients
        ↓
[recommend.py] → structured recommendation (price, direction, %)
        ↓
[llm_reasoning.py] → natural-language justification (Groq LLM)
        ↓
[streamlit_app.py] → interactive dashboard (UI)
```

See [`architecture.txt`](architecture.txt) for the full annotated diagram.

---

## Folder Structure

```
pricing-intelligence-agent/
├── data/
│   ├── generate_data.py        # synthetic dataset generator
│   └── pricing_data.csv        # generated on first run
├── analysis/
│   ├── __init__.py
│   ├── elasticity.py           # log-log regression per category
│   ├── recommend.py            # recommendation engine
│   └── llm_reasoning.py        # LLM justification layer
├── app/
│   └── streamlit_app.py        # Streamlit UI
├── tests/
│   └── test_recommend.py       # pytest unit tests
├── requirements.txt
├── .env.example
├── README.md
└── architecture.txt
```

---

## Setup Instructions

### 1. Clone & install

```bash
git clone <Pricing-Intelligence-Agent>
cd pricing-intelligence-agent

# Create virtual environment (Python 3.11 recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure API key (optional — app works without it)

```bash
cp .env.example .env
# Open .env and set your Groq API key:
# GROQ_API_KEY=gsk_...
```

Get a free Groq API key at <https://console.groq.com/keys>.
The app falls back to a deterministic rule-based justification if no key is set.

### 3. Generate the dataset

```bash
python data/generate_data.py
```

### 4. Run the app

```bash
streamlit run app/streamlit_app.py
```

Visit <http://localhost:8501>.

---


## Elasticity Methodology

### Log-log OLS Regression

For each product category we fit:

```
log(units_sold) = α + β · log(your_price) + ε
```

The slope coefficient **β** is the **price elasticity of demand**:
- β = −1.5 means a 1 % price increase leads to a 1.5 % decrease in units sold.
- Values between 0 and −0.6 are considered **inelastic** (demand is relatively stable).
- Values below −1.2 are considered **elastic** (demand is highly price-sensitive).

This log-log specification is standard in econometrics because the coefficient is
directly interpretable as an elasticity — a pure ratio, independent of units.

### Why synthetic data?

| Reason | Explanation |
|---|---|
| **ToS risk** | Scraping competitor prices violates most retailers' terms of service. |
| **Reproducibility** | A fixed random seed (42) guarantees identical results across machines. |
| **Controllable ground truth** | We bake in known elasticity values per category, so we can validate that the OLS model recovers them and that R² is meaningfully high. |
| **Privacy** | No real customer purchase data is stored or transmitted. |

---

## Recommendation Decision Logic

| Condition | Action |
|---|---|
| `\|elasticity\| < 0.6` AND `your_price ≤ competitor_price` | **Raise** price by `min(8%, \|gap\|×50%)` |
| `\|elasticity\| ≥ 1.2` AND `your_price > competitor_price + 5%` | **Lower** price by `min(10%, gap×50%)` |
| Otherwise | **Hold** |
| Always | Enforce ≥ 10% gross margin floor |

---

## Running Tests

```bash
pytest tests/ -v
```

All 6 unit tests should pass:
- Required keys present in recommendation dict
- Suggested price never violates 10% margin floor
- All category elasticities are negative (economic sanity)
- Direction is a valid enum value
- All prices are positive
- Hold direction leaves price unchanged

---

## HuggingFace Spaces Deployment

1. Create a new Space at <https://huggingface.co/spaces> with **Streamlit** SDK.
2. Push this repository to the Space:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/<space-name>
   git push space main
   ```
3. In the Space settings, add `GROQ_API_KEY` as a **Secret**.
4. The Space will auto-install `requirements.txt` and run `app/streamlit_app.py`.

> **Note:** HuggingFace Spaces does not persist files between restarts. The app calls
> `generate_data.py` logic lazily on startup via `st.cache_data` — or you can commit
> `data/pricing_data.csv` directly to the repo for zero-startup-cost deploys.

---

## Future Extensions

| Extension | Description |
|---|---|
| **Real-time competitor feeds** | Integrate with a price intelligence API (e.g., Prisync, Wiser) to replace synthetic competitor prices with live data. |
| **BigQuery ingestion** | Stream transactional data from BigQuery using the BigQuery Storage API, replacing the CSV layer with a live warehouse connection. |
| **A/B testing validation** | Deploy price recommendations as treatment variants in a split-test framework (e.g., GrowthBook) and measure realized elasticity vs. model predictions. |
| **Multi-market segmentation** | Extend the elasticity model to segment by geography, customer tier, or channel (marketplace vs. direct). |
| **Automated repricing API** | Expose recommendations via a FastAPI endpoint for downstream integration with ERP/PIM systems. |

---

## Engineering Assumptions

- **Synthetic data** is used instead of live price feeds (ToS safety + reproducibility).
- **26 weekly observations per SKU** is the minimum for a stable OLS regression with log-log transformation; more history improves R².
- **Groq's free tier** is used for LLM calls because it supports the OpenAI SDK interface and provides generous rate limits at zero cost.
- **Streamlit** is chosen over FastAPI + React because the target persona (pricing analyst) expects a notebook-like interactive tool, not a full web app.
- **Margin floor** (10%) is a conservative default; production systems would read this from a product-category config.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Built as a portfolio project demonstrating Data Analyst — Pricing skills:
elasticity modelling, recommendation engines, LLM integration, and analytics dashboards.*
