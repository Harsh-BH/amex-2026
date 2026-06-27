---
name: feature-selection
description: Use when deciding which features enter the profitability equation and which to drop. Selection here is business-driven (P&L relevance) plus signal quality, not a black-box importance ranking.
---

# Feature Selection

## Purpose
Choose a parsimonious, interpretable feature set that maps to real revenue/cost, dropping noise and redundancy.

## Inputs
`feature-notes.md` (roles, missingness), EDA correlations, `business-context.md`.

## Outputs
An in/out decision per feature with rationale (→ writeup "Variable Selection Logic").

## Invocation Conditions
- During framework design; whenever adding/removing a term.

## Workflow
1. **Mandatory excludes:** `id` (always); constant-fee logic (no signal within product).
2. **P&L relevance:** keep features that clearly book revenue/cost/risk; justify each.
3. **Signal quality:** down-weight or drop very-sparse features (`f23` 88% missing) unless they help the top tail.
4. **Redundancy:** if two features are collinear (e.g. `f17`/`f18` lend lines), keep the more informative or combine.
5. **Top-tier test:** does the feature actually help separate the top 20%? If not, it's dead weight.

## Best Practices
- Fewer, well-justified terms beat a kitchen sink (interpretability + private-LB robustness).
- Selection rationale must be writeup-ready.

## Common Mistakes
- Keeping features "because they correlate" without a P&L story.
- Dropping a structurally-missing feature instead of encoding the missingness as signal.

## Example Usage
"Should f18 stay if f17 is in?" → check correlation; if near-redundant, keep `f17` (total) + a consumer-share ratio, drop raw `f18`.
