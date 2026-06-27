# Workflow 09 — Framework Design

**Objective:** The explicit revenue−cost equation that scores profitability, with every term justified.
**Prerequisites:** Workflows 03–07.

## Steps
1. Invoke **profitability-framework-design** (`/train`).
2. Structure P&L: revenue terms − cost terms; map features; apply transforms + missing rules.
3. Normalize all terms; assemble a single continuous, sign-correct score in `src/scoring.py`.
4. Hand-built ranking check: a high-spend/low-risk row outranks a low-spend/high-cost row.
5. Draft the `framework-doc.md` in lockstep with the code.

## Validation
- Equation is interpretable; each term maps to a real revenue/cost; no `id`; score separates the top tail.

## Deliverables
- `src/scoring.py` v1 + framework writeup draft.

## Exit criteria
- A scored 500K candidate ready for calibration + evaluation.
