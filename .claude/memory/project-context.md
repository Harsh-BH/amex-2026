# Project Context

_Living summary of what this project is. Update when scope or stage changes._

## What
American Express Campus Challenge 2026, **Round 1** — rank 500K Premier cardmembers by
**profitability to the issuer** and submit a per-`id` score + a written Profitability Framework.

## Why it's unusual
- **No target variable.** The data has only cardmember attributes (`f1`–`f23`). We are NOT
  training a supervised model against a known profit label — we are **designing an
  interpretable revenue−cost framework** whose ranking matches Amex's hidden ground truth.
- Grading rewards **top-20% overlap** (not global rank) and a **defensible business writeup**
  (not raw accuracy).

## Deliverables (R1)
1. `Predictions` sheet: `ID, Prediction` for **all 500,000** rows.
2. `Profitability Framework` sheet: Variables Used, Equation, Prediction Logic, Variable
   Selection Logic, Coefficient/Weight Derivation, Feature Transformations, Business Logic,
   Assumptions, Validation Approach, Notes.

## Evaluation
- Accuracy = % of Actual Top-20% profitable CMs captured in our Top-20% by score.
- Data split 70/30: **public LB = 70%** (live), **private LB = 30%** (hidden, decides placement).
- **≤10 submissions**, best score counts.

## Stage tracker
- [x] Phase: Deep problem understanding (complete — see decision-log 2026-06-26).
- [x] Phase: `.claude` operating system built.
- [ ] Phase: Environment setup (pandas/openpyxl broken in sandbox — verify).
- [ ] Phase: EDA + missing-value strategy.
- [ ] Phase: Framework design + weight calibration.
- [ ] Phase: Score 500K + validate top-20% + first submission.
- [ ] Phase: Iterate (≤10) + final documentation.

## Tooling
- **EDA:** `src/eda.py` (`PremierEDA` class + `add_features`), notebook `notebooks/eda.ipynb`. Env: `.venv` (py3.14, pandas 3.0). Data pickle-cached at `data/premier.pkl`.
- **LLM cell explanations:** `src/eda.py`-paired `src/explain.py` → `show(obj, "label")` displays a table/chart AND an OpenAI plain-English explanation (text=gpt-4o-mini, charts=gpt-4o vision). stdlib `urllib`, no `openai` dep. **`OPENAI_API_KEY` lives in `.env` (gitignored)** — user shared it in chat, so rotate when convenient.

## Key files
- Data: `docs/6a3cb6104933b_campus_challenge_r1_data.xlsx`
- Dictionary: `docs/6a3cb624df197_feature_description.xlsx`
- Submission template: `docs/6a3cb64c7cae4_campus_challenge_r1_submission_template.xlsx`
- Problem statement: `docs/6a3cb67628b27_campus_challenge26_r1.pdf`
