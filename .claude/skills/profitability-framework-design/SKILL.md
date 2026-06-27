---
name: profitability-framework-design
description: THE core skill. Use when designing or revising the revenue-minus-cost equation that scores each cardmember's profitability. Invoke whenever building the scoring logic or the Framework writeup. This problem is framework design, not model training.
---

# Profitability Framework Design

## Purpose
Build the explicit, interpretable equation `profit_score = Σ wᵢ · gᵢ(features)` that rank-orders the 500K members by profitability-to-issuer, and that defends as real card economics.

## Inputs
`business-context.md` (revenue/cost levers), engineered features, EDA evidence, `assumptions.md`.

## Outputs
A scoring equation in `src/scoring.py` + the completed `templates/framework-doc.md`. Continuous score per `id`.

## Invocation Conditions
- The central activity of R1. Any change to scoring logic goes through here.

## Workflow
1. **Structure the P&L:** revenue terms (spend-margin, interest on revolve/lend, supp fees) **minus** cost terms (rewards, benefit credits, expected loss, servicing).
2. **Map features to terms** (from business-analysis). Apply transforms (feature-engineering) and missing rules.
3. **Normalize** all terms to comparable scale before weighting.
4. **Assign weights** with a business rationale (weight-calibration skill refines them). No magic numbers.
5. **Combine** into a single continuous score; ensure sign-correctness (revenue ↑ score, cost ↓ score).
6. **Validate** top-20% stability (evaluation skill) and business plausibility of the top members.
7. **Document** every term in the writeup as you go.

## Best Practices
- Interpretable & scalable beats opaque-but-higher-public-LB (private 30% + integrity audit).
- Keep it a transparent weighted sum unless a decision-log entry justifies more complexity.
- Re-derive, don't hardcode: weights traceable to reasoning/calibration.

## Common Mistakes
- Reframing as supervised ML against an invented label.
- Adding spend as pure profit without its rewards/benefit cost.
- Letting one huge-scale term (`f4`) dominate via missing normalization.
- Optimizing global rank instead of top-tier separation.

## Example Usage
"Draft v1 of the framework." → revenue = log spend + risk-adjusted interest + supp; cost = rewards/spend ratio + benefit credits + loss term; combine, normalize, weight, validate top-20%.
