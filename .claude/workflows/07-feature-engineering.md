# Workflow 07 — Feature Engineering

**Objective:** Transformed/derived features (scales, margin ratios, risk adjustments, flags) for the equation.
**Prerequisites:** Workflows 05, 06.

## Steps
1. Invoke **feature-engineering** (`/features`).
2. Normalize heavy tails; build margin-proxy ratios; risk-adjust revenue terms; add structural flags.
3. Invoke **feature-selection** to keep a parsimonious, P&L-justified set.
4. Document each derived feature (`feature-doc.md`) with a runnable check.

## Validation
- Transforms are interpretable, sign-correct, and on comparable scales.

## Deliverables
- `src/features.py` derived features + selection rationale.

## Exit criteria
- A clean, justified feature set ready to assemble into the score.
